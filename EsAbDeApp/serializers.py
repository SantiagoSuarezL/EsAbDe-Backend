from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from EsAbDeApp.models import Personas, Evaluacion, Respuesta, User, Pacientes, Areas
from datetime import date

class LoginSerializer(serializers.Serializer):
  username = serializers.CharField()
  password = serializers.CharField()

  def validate(self, data):
    username = data.get('username')
    password = data.get('password')

    user = authenticate(username=username, password=password)

    if user and user.is_active:
      return user
    raise serializers.ValidationError("Credenciales incorrectas.")
  
User = get_user_model()
  
class RegisterSerializer(serializers.Serializer):
  username = serializers.CharField()
  password = serializers.CharField(write_only=True)
  email = serializers.EmailField(required=False)

  class Meta:
    model = User
    fields = ['username', 'email', 'password']

  def create(self, validated_data):
    user = User(
      username=validated_data['username'],
      email=validated_data['email']
    )
    user.set_password(validated_data['password'])
    user.save()
    return user
  
class PersonasSerializer(serializers.ModelSerializer):
  class Meta:
    model = Personas
    fields = ['nombre', 'email', 'area_encargada']

  def create(self, validated_data):
    validated_data['user'] = self.context['request'].user
    return Personas.objects.create(**validated_data)
  
class RespuestaSerializer(serializers.ModelSerializer):
  class Meta:
    model = Respuesta
    fields = ['score', 'description']
  
class AreasSerializer(serializers.ModelSerializer):
  respuestas = RespuestaSerializer(many=True)

  class Meta:
    model = Areas
    fields = ['nameArea', 'score', 'description', 'respuestas']
    extra_kwargs = {
      'score': {'read_only': True},
      'description': {'required': False},
    }

  def create(self, validated_data):
    if 'description' not in validated_data or not validated_data['description']:
      validated_data['description'] = "No hay una descripción disponible"

    validated_data['score'] = 0
    return super().create(validated_data)
  
class PacienteSerializer(serializers.ModelSerializer):
  # areas = AreasSerializer(source='area', many=True)

  class Meta:
    model = Pacientes
    fields = ['id', 'first_name', 'second_name', 'last_name', 'second_last_name', 'gender', 'birthdate']

  def create(self, validated_data):
    paciente_id = validated_data.get('id')
    if Pacientes.objects.filter(id=paciente_id).exists():
      raise serializers.ValidationError("El paciente ya existe.")

    if validated_data['gender'] == "Male":
      validated_data['gender'] = "Masculino"
    elif validated_data['gender'] == "Female":
      validated_data['gender'] = "Femenino"

    return super().create(validated_data)

  def validate_birthdate(self, value):
    if value > date.today():
      raise serializers.ValidationError("La fecha de nacimiento no puede ser mayor a la fecha actual.")
    return value
  
class EvaluacionSerializer(serializers.ModelSerializer):
  patient = serializers.PrimaryKeyRelatedField(queryset=Pacientes.objects.all())
  area = serializers.PrimaryKeyRelatedField(queryset=Areas.objects.all())
  birthdate = serializers.DateField(required=True)

  class Meta:
    model = Evaluacion
    fields = ['patient', 'area', 'birthdate']