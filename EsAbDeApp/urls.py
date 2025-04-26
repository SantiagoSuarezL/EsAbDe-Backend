from django.urls import path
from . import views

urlpatterns = [
  path('login/', views.LoginView.as_view(), name='login'),
  path('register/', views.RegisterView.as_view(), name='register'),
  path('logout/', views.LogoutView.as_view(), name='logout'),
  path('profile/', views.PerfilView.as_view(), name='personas'),
  path('personas/', views.PersonasCreateView.as_view(), name='personas_create'),
  path('create/pacientes/', views.PacientesCreateView.as_view(), name='pacientes_create'),
  path('update/patient/<int:paciente_id>/', views.PatientUpdateView.as_view(), name='pacientes_update'),
  path('delete/patient/<int:paciente_id>/', views.PatientDeleteView.as_view(), name='pacientes_delete'),
  path('get/pacientes/', views.PacientesListView.as_view(), name='pacientes_get'),
  path('areas/', views.AreasCreateView.as_view(), name='areas_create'),
  path('get/areas/', views.AreasListView.as_view(), name='areas_get'),
  path('pacientes/<int:paciente_id>/<int:area_id>/', views.PatientAreaDetailView.as_view(), name='pacientes_areas'),
  path('get/paciente/<int:paciente_id>/', views.PatientIdDetailView.as_view(), name='pacientes_detail'),
  path('evaluar/', views.EvaluationPatient.as_view(), name='evaluar'),
  path('generate/', views.GenerativeAIView.as_view(), name='generate'),
  path('upload/', views.UploadFileView.as_view(), name='upload'),
]

