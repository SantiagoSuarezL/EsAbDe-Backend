from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from EsAbDeApp.models import Personas, User, Pacientes, Areas
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
  
class PacienteSerializer(serializers.ModelSerializer):
  class Meta:
    model = Pacientes
    fields = ['first_name', 'second_name', 'last_name', 'second_last_name', 'gender', 'birthdate', 'area']

  def validate_birthdate(self, value):
    if value > date.today():
      raise serializers.ValidationError("La fecha de nacimiento no puede ser mayor a la fecha actual.")
    return value
  
class AreasSerializer(serializers.ModelSerializer):
  class Meta:
    model = Areas
    fields = ['nameArea', 'score', 'description']
    extra_kwargs = {
      'score': {'read_only': True},
      'description': {'required': False},
    }

  def create(self, validated_data):
    if 'description' not in validated_data or not validated_data['description']:
      validated_data['description'] = "No hay una descripción disponible"

    validated_data['score'] = 0
    return super().create(validated_data)