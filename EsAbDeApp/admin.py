from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
  list_display = ('username', 'email', 'failed_attempts', 'last_failed_attempt', 'is_active', 'is_staff') 
  search_fields = ('username', 'email')
  list_filter = ('is_active', 'is_staff')

  fieldsets = (
    (None, {
        'fields': ('username', 'email', 'failed_attempts', 'last_failed_attempt', 'is_active', 'is_staff')
    }),
    ('Contraseña', {
        'fields': ('password',)
    }),
  )

  add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('username', 'email', 'password1', 'password2', 'is_active', 'is_staff')}
    ),
  )