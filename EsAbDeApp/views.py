from datetime import timedelta, timezone
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import login
from EsAbDeApp.models import User
from .serializers import LoginSerializer, RegisterSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

class LoginView(APIView):
  @swagger_auto_schema(
    tags= ['API de EsAbDe'],
    operation_summary="Iniciar sesión",
    operation_description="Permite a un usuario iniciar sesión con sus credenciales.",
    request_body=LoginSerializer,
    responses={200: 'Inicio de sesión exitoso.', 401: 'Credenciales incorrectas.', 403: 'Cuenta bloqueada.'}
  )
  def post(self, request, *args, **kwargs):
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
      user = serializer.validated_data

      if user.is_locked_out():
        lockout_time_remaining = user.last_failed_attempt + timedelta(minutes=5) - timezone.now()
        return Response({
          'message': f'Cuenta bloqueada. Inténtalo de nuevo en {lockout_time_remaining.seconds // 60} minutos.'
        }, status=status.HTTP_403_FORBIDDEN)

      user.reset_failed_attempts()
      login(request, user)
      return Response({'message': 'Inicio de sesión exitoso.'}, status=status.HTTP_200_OK)
    
    username = request.data.get('username')
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