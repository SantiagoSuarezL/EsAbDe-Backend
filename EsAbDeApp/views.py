from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone as django_timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import AreasSerializer, EvaluacionSerializer, LoginSerializer, PacienteSerializer, PersonasSerializer, RegisterSerializer
from datetime import timedelta
from EsAbDeApp.models import User
from .models import AgeRange, Areas, Pacientes, Pregunta, Respuesta
from datetime import datetime
import logging
import os
import google.generativeai as genai
from django.http import JsonResponse

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class GenerativeAIView(APIView):
  def post(self, request):
    logging.info(f"Datos recibidos: {request.data}")

    puntaje = request.data.get('puntaje')
    patient_id = request.data.get('patient_id')
    area_id = request.data.get('area_id')

    if puntaje is None or patient_id is None or area_id is None:
      logging.error("Falta en los datos",request.data)
      return JsonResponse({"error": "Faltan datos en la solicitud"}, status=400)
    
    try:
      logging.info(f"patient_id: {patient_id}")
      patient = Pacientes.objects.get(id=patient_id)
      area = Areas.objects.get(id=area_id)
    except Pacientes.DoesNotExist or Areas.DoesNotExist:
      return JsonResponse({"error": "Paciente o área no encontrados"}, status=404)
    
    prompt =(
              "Eres un médico pediatra experto en desarrollo infantil."
              "Genera una observacion de acuerdo con los siguientes niveles de puntaje en el area de"
              f"{area.nameArea}"
              "- Si el puntaje es 99: el desarrollo del niño o niña es el esperado para su edad.\n"
              "- Si el puntaje es 66: el niño o niña está en riesgo de problemas de desarrollo.\n"
              "- Si el puntaje es 33 o 0: el niño o la niña podría experimentar un retraso en el desarrollo.\n\n"
              f"El puntaje del paciente es {puntaje}. Proporciona una observación clara y breve sobre el estado de desarrollo del paciente sin ningun texto adicional."
            )

    generation_config = {
      "temperature": 0.7,
      "top_p": 0.9,
      "top_k": 40,
      "max_output_tokens": 200,
      "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
      model_name="gemini-1.5-flash",
      generation_config=generation_config,
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)

    respuesta = Respuesta(
      patient=patient,
      area=area,
      score=puntaje,
      description=response.text
    )
    respuesta.save()

    return JsonResponse({"observacion": response.text, "respuesta_id": respuesta.id})

logging.basicConfig(
  filename='logs.log',
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LoginView(APIView):
  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Iniciar sesión",
    operation_description="Permite a un usuario iniciar sesión con sus credenciales.",
    request_body=LoginSerializer,
    responses={200: 'Inicio de sesión exitoso.', 401: 'Credenciales incorrectas.', 403: 'Cuenta bloqueada.'}
  )
  def post(self, request, *args, **kwargs):    
    username = request.data.get('username')
    password = request.data.get('password')

    user = User.objects.filter(username=username).first()

    if user is not None and user.is_locked_out():
      lockut_time_remaining = user.last_failed_attempt + timedelta(minutes=5) - django_timezone.now()
      return Response({'message': f'Cuenta bloqueada. Intente de nuevo en {lockut_time_remaining.seconds//60} minutos.'}, status=status.HTTP_403_FORBIDDEN)
    
    user = authenticate(username=username, password=password)

    if user is not None:
      user.reset_failed_attempts()
      refresh = RefreshToken.for_user(user)
      return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token)
      }, status=status.HTTP_200_OK)

    if user is None:
      user = User.objects.filter(username=username).first()
      if user:
        user.register_failed_attempt()
    return Response({'message': 'Credenciales incorrectas.'}, status=status.HTTP_401_UNAUTHORIZED)
  
class RegisterView(APIView):
  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Registrar usuario",
    operation_description="Permite a un usuario registrarse en la aplicación.",
    request_body=RegisterSerializer,
    responses={201: 'Usuario registrado.', 400: 'Datos incorrectos.'}
  )
  def post(self, request, *args, **kwargs):
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
      user = serializer.save()
      return Response({'message': 'Usuario registrado.'}, status=status.HTTP_201_CREATED)

    return Response({'message': 'Datos incorrectos.'}, status=status.HTTP_400_BAD_REQUEST)
  
class LogoutView(APIView):
  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Cerrar sesión",
    operation_description="Permite a un usuario cerrar sesión.",
    responses={200: 'Sesión cerrada.'}
  )
  def post(self, request):
    try:
      refresh_token = request.data['refresh']
      token = RefreshToken(refresh_token)
      token.blacklist()
      return Response({'message': 'Sesión cerrada.'}, status=status.HTTP_200_OK)
    except:
      return Response({'message': 'Token inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    
class PerfilView(APIView):
  permission_classes = [IsAuthenticated]

  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Obtener perfil",
    operation_description="Permite obtener el perfil del usuario que inicia sesion.",
    responses={200: PersonasSerializer}
  )
  def get(self, request):
    if hasattr(request.user, 'personas'):
      persona = request.user.personas
      serializer = PersonasSerializer(persona)
      return Response(serializer.data)
    else:
      return Response({"detail": "No hay información de personas asociada a este usuario."}, status=404)
    
class PersonasCreateView(APIView):
  permission_classes = [IsAuthenticated]

  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Crear persona",
    operation_description="Permite a un administrador crear una persona.",
    request_body=PersonasSerializer,
    responses={201: PersonasSerializer, 400: 'Datos incorrectos.'}
  )

  def post(self, request):
    serializer = PersonasSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  
class PacientesCreateView(APIView):
  permission_classes = [IsAuthenticated]

  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Crear paciente",
    operation_description="Permite a un administrador crear un paciente.",
    request_body=PacienteSerializer,
    responses={201: PacienteSerializer, 400: 'Datos incorrectos.'}
  )

  def post(self, request):
    logging.info(f"request_post: {request.data}")
    serializer = PacienteSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():

      paciente = serializer.save(created_by=request.user.personas)

      areas = Areas.objects.all()
      paciente.area.set(areas)

      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientUpdateView(APIView):
  permission_classes = [IsAuthenticated]

  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Actualizar paciente",
    operation_description="Permite a un administrador actualizar un paciente.",
    request_body=PacienteSerializer,
    responses={200: PacienteSerializer, 400: 'Datos incorrectos.'}
  )

  def put(self, request, paciente_id):
    try:
      paciente = Pacientes.objects.get(id=paciente_id)
    except Pacientes.DoesNotExist:
      return Response({'message': 'Paciente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = PacienteSerializer(paciente, data=request.data, context={'request': request})
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientDeleteView(APIView):
  permission_classes = [IsAuthenticated]

  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Eliminar paciente",
    operation_description="Permite a un administrador eliminar un paciente.",
    responses={204: 'Paciente eliminado.', 404: 'Paciente no encontrado.'}
  )

  def delete(self, request, paciente_id):
    try:
      paciente = Pacientes.objects.get(id=paciente_id)
      paciente.delete()
      return Response({'message': 'Paciente eliminado.'}, status=status.HTTP_204_NO_CONTENT)
    except Pacientes.DoesNotExist:
      return Response({'message': 'Paciente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
  
class PacientesListView(APIView):
  permission_classes = [IsAuthenticated]

  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Listar pacientes",
    operation_description="Permite a un administrador listar los pacientes.",
    responses={200: PacienteSerializer}
  )

  def get(self, request):
    pacientes = Pacientes.objects.filter(created_by=request.user.personas).prefetch_related('area')

    patient_data = []
    for paciente in pacientes:
      areas_data = []
      for area in paciente.area.all():
        respuestas = Respuesta.objects.filter(patient=paciente, area=area)
        respuestas_data = [{
          'score': respuesta.score,
          'description': respuesta.description if respuesta.description else 'No hay observaciones disponibles.'
        } for respuesta in respuestas]
        
        areas_data.append({
          'nameArea': area.nameArea,
          'respuestas': respuestas_data
        })

      patient_data.append({
        'id': paciente.id,
        'first_name': paciente.first_name,
        'second_name': paciente.second_name,
        'last_name': paciente.last_name,
        'second_last_name': paciente.second_last_name,
        'gender': paciente.gender,
        'birthdate': paciente.birthdate,
        'areas': areas_data
      })
    return Response(patient_data, status=status.HTTP_200_OK)
  
class AreasCreateView(APIView):

  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Crear área",
    operation_description="Permite a un administrador crear un área.",
    responses={201: AreasSerializer, 400: 'Datos incorrectos.'}
  )

  def post(self, request):
    serializer = AreasSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def calculate_age(birthdate):
    now = datetime.now().date()
    years = now.year - birthdate.year
    months = now.month - birthdate.month
    days = now.day - birthdate.day

    if months < 0:
        years -= 1
        months += 12

    if days < 0:
        months -= 1
        last_month = (now.month - 1) if now.month > 1 else 12
        days += (datetime(now.year, last_month, 1) - datetime(now.year, last_month - 1, 1)).days

    return {"years": years, "months": months, "days": days}

  
class AreasListView(APIView):

  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Listar áreas",
    operation_description="Permite a un administrador listar las áreas.",
    responses={200: AreasSerializer}
  )

  def get(self, request):
    areas = Areas.objects.values('id','nameArea')
    return Response(areas, status=status.HTTP_200_OK)
  
  
class PatientAreaDetailView(APIView):
  def get(self, request, paciente_id, area_id):
    try:
      paciente = Pacientes.objects.get(id=paciente_id)
      area = Areas.objects.get(id=area_id, pacientes=paciente)

      paciente_data = PacienteSerializer(paciente).data
      area_data = AreasSerializer(area).data

      edad_data = calculate_age(paciente.birthdate)

      return Response ({
        'paciente': paciente_data,
        'area': area_data,
        'edad': edad_data
      }, status=status.HTTP_200_OK)
    except Pacientes.DoesNotExist:
      return Response({'message': 'Paciente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Areas.DoesNotExist:
      return Response({'message': 'Área no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    
class PatientIdDetailView(APIView):
  def get(self, request, paciente_id):
    try:
      paciente = Pacientes.objects.get(id=paciente_id)

      paciente_data = PacienteSerializer(paciente).data

      edad_data = calculate_age(paciente.birthdate)

      return Response ({
        'paciente': paciente_data,
        'edad': edad_data
      }, status=status.HTTP_200_OK)
    except Pacientes.DoesNotExist:
      return Response({'message': 'Paciente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
class EvaluationPatient(APIView):
    def post(self, request):
        logging.info(f"request: {request.data}")  # Muestra la solicitud entrante
        serializer = EvaluacionSerializer(data=request.data)
        
        if serializer.is_valid():
            logging.info("Datos validados:", serializer.validated_data)
            birthdate = serializer.validated_data['birthdate']
            age_in_days = (datetime.now().date() - birthdate).days
            
            age_range = AgeRange.objects.filter(min_days__lte=age_in_days, max_days__gte=age_in_days).first()
            if not age_range:
                return Response({"error": "No se encontró un rango de edad adecuado"}, status=status.HTTP_400_BAD_REQUEST)
                
            area = serializer.validated_data['area']
            preguntas = Pregunta.objects.filter(age_range=age_range, area=area)
            preguntas_data = [{"question": pregunta.question} for pregunta in preguntas]
                
            return Response({"preguntas": preguntas_data}, status=status.HTTP_200_OK)
        else: 
          logging.error("Errores de validación:", serializer.errors)
          return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
