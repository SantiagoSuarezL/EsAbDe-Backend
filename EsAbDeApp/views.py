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
from .models import AgeRange, Areas, Pacientes, Pregunta
from datetime import datetime
import logging

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
        areas_data.append({
          'nameArea': area.nameArea,
          'score': area.score,
          'description': area.description if area.description else 'No hay observaciones disponibles.'
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
