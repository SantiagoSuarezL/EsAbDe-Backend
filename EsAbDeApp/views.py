from django.contrib.auth import authenticate
from django.utils import timezone as django_timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import LoginSerializer, PersonasSerializer, RegisterSerializer
from datetime import timedelta
from EsAbDeApp.models import User

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