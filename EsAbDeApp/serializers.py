from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from EsAbDeApp.models import User

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