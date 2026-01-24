from django.urls import path
from .views import student_views, course_views

app_name = 'curso'

# URLs públicas para el estudiante
public_patterns = [
    path('portal/', student_views.PublicPortalView.as_view(), name='public_portal'),
    path('buscar/', student_views.CertificateSearchView.as_view(), name='certificate_search'),
    path('descargar/<int:pk>/', student_views.CertificateDownloadView.as_view(), name='certificate_download'),
    path('verificar/<str:code>/', student_views.CertificateVerifyView.as_view(), name='public_verify'),
]

urlpatterns = [
    # URLs de administración
    path('', course_views.CursoListView.as_view(), name='list'),
    path('crear/', course_views.CursoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', course_views.CursoUpdateView.as_view(), name='edit'),
    path('eliminar/<int:pk>/', course_views.CursoDeleteView.as_view(), name='delete'),
    path('configurar-certificado/<int:pk>/', course_views.CursoCertificateConfigView.as_view(), name='config'),
    path('estudiantes/<int:pk>/', course_views.CursoEstudiantesView.as_view(), name='estudiantes'),
    path('estudiantes/nuevo/<int:pk>/', course_views.EstudianteCreateView.as_view(), name='estudiante_add'),
    path('estudiantes/editar/<int:pk>/', course_views.EstudianteUpdateView.as_view(), name='estudiante_edit'),
    path('estudiantes/eliminar/<int:pk>/', course_views.EstudianteDeleteView.as_view(), name='estudiante_delete'),
    path('generar-certificado/<int:pk>/', course_views.GenerarCertificadoView.as_view(), name='generar_individual'),
    path('generar-todos/<int:pk>/', course_views.GenerarTodosCertificadosView.as_view(), name='generar_todos'),
    path('descargar-zip/<int:pk>/', course_views.DescargarCertificadosZipView.as_view(), name='descargar_zip'),

    # URLs de plantillas
    path('plantillas/', course_views.PlantillaListView.as_view(), name='plantilla_list'),
    path('plantillas/crear/', course_views.PlantillaCreateView.as_view(), name='plantilla_create'),
    path('plantillas/editar/<int:pk>/', course_views.PlantillaUpdateView.as_view(), name='plantilla_edit'),
    path('plantillas/eliminar/<int:pk>/', course_views.PlantillaDeleteView.as_view(), name='plantilla_delete'),
] + public_patterns
