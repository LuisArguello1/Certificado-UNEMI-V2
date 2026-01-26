"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),  # Core app (dashboard) at ROOT
    path('correo/', include('apps.correo.urls')),  # Correo app
    path('curso/', include('apps.curso.urls')),    # Curso app
    path('auth/', include('apps.accounts.urls')),  # Accounts app
]

if settings.DEBUG:
    # Include django_browser_reload URLs solo en modo DEBUG 
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    # Servir archivos media en desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

