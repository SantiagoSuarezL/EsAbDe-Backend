from datetime import timedelta, timezone
from django.contrib.auth.models import AbstractUser
from django.db import models

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
      lockout_time = self.last_failed_attempt + timedelta(minutes=5)
      if timezone.now() < lockout_time:
        return True
    return False
  
  def reset_failed_attempts(self):
    self.failed_attempts = 0
    self.last_failed_attempt = None
    self.save()

  def register_failed_attempt(self):
    self.failed_attempts += 1
    self.last_failed_attempt = timezone.now()
    self.save()