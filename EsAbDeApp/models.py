from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone as django_timezone

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
