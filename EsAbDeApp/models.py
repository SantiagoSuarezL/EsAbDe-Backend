from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone as django_timezone
from django.conf import settings

class User(AbstractUser):
  failed_attempts = models.IntegerField(default=0)
  last_failed_attempt = models.DateTimeField(null=True, blank=True)

  groups = models.ManyToManyField(
    'auth.Group',
    related_name='custom_user_groups',
    blank=True
    )
  user_permissions = models.ManyToManyField(
    'auth.Permission',
    related_name='custom_user_permissions',
    blank=True
    )

  def is_locked_out(self):
    if self.failed_attempts >= 5:
      lockout_duration = django_timezone.now() - self.last_failed_attempt
      return lockout_duration.total_seconds() < 300
    return False

  def reset_failed_attempts(self):
    self.failed_attempts = 0
    self.last_failed_attempt = None
    self.save()

  def register_failed_attempt(self):
    self.failed_attempts += 1
    self.last_failed_attempt = django_timezone.now()
    self.save()

class Personas(models.Model):
  user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='personas'
  )
  nombre = models.CharField(max_length=100)
  email = models.EmailField()
  area_encargada = models.CharField(max_length=100)

  def __str__(self):
      return self.nombre
  
class Areas (models.Model):
  nameArea = models.CharField(max_length=100)
  score = models.IntegerField(default=0)
  description = models.TextField(blank=True, null=True)

  def __str__(self):
    return self.nameArea
  
class Pacientes (models.Model):
  first_name = models.CharField(max_length=100)
  second_name = models.CharField(max_length=100, blank=True, null=True)
  last_name = models.CharField(max_length=100)
  second_last_name = models.CharField(max_length=100, blank=True, null=True)
  gender = models.CharField(max_length=10)
  birthdate = models.DateField(null=True, blank=True)
  created_by = models.ForeignKey(Personas, on_delete=models.CASCADE, related_name='pacientes')
  created_at = models.DateTimeField(auto_now_add=True)
  area = models.ManyToManyField(Areas, related_name='pacientes', blank=True)

  def clean(self):
    super().clean()
    if self.birthdate > django_timezone.now().date():
     raise ValidationError("La fecha de nacimiento no puede ser futura.")