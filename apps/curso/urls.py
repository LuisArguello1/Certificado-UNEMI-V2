from django.urls import path
from .views import student_views

app_name = 'curso'

# URLs públicas para el estudiante
public_patterns = [
    path('portal/', student_views.PublicPortalView.as_view(), name='public_portal'),
    path('buscar/', student_views.CertificateSearchView.as_view(), name='certificate_search'),
    path('descargar/<int:pk>/', student_views.CertificateDownloadView.as_view(), name='certificate_download'),
]

urlpatterns = [
    # Aquí irían las URLs de administración del curso (a implementar por su compañera)
    # Por ejemplo:
    # path('', ... name='list'),
] + public_patterns
