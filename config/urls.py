import environ
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.certificado.views.public_views import ValidacionCertificadoView

env = environ.Env()

urlpatterns = [
    # URL de admin protegida (configurable en .env)
    path(env('ADMIN_URL', default='admin/'), admin.site.urls),
    path('', include('apps.core.urls')),  
    path('certificados/', include('apps.certificado.urls')), 
    path('auth/', include('apps.accounts.urls')), 
    
    # Ruta de validación QR
    path('validar/<uuid:uuid>/', ValidacionCertificadoView.as_view(), name='validar_certificado'),
]

if settings.DEBUG: 
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

