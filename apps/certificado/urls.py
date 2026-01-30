"""
URLs para la app de certificados.
"""

from django.urls import path
from .views import (
    CertificadoCreateView,
    ProcesamientoStatusView,
    EventoDetailView,
    CertificadoListView,
    CertificadoPreviewView,
    get_variantes_api,
    get_plantillas_api
)
from .views.plantilla_views import (
    PlantillaListView,
    PlantillaDetailView,
    PlantillaCreateView,
    PlantillaUpdateView,
    PlantillaDeleteView
)
from .views.direccion_views import (
    DireccionListView,
    DireccionDetailView,
    DireccionCreateView,
    DireccionUpdateView,
    DireccionDeleteView,
    DireccionToggleActiveView
)
from .views.catalogo_views import (
    ModalidadListView, 
    ModalidadCreateView, 
    ModalidadUpdateView, 
    ModalidadDeleteView, 
    ModalidadToggleActiveView,
    TipoListView, 
    TipoCreateView, 
    TipoUpdateView, 
    TipoDeleteView, 
    TipoToggleActiveView,
    TipoEventoListView, 
    TipoEventoCreateView, 
    TipoEventoUpdateView, 
    TipoEventoDeleteView, 
    TipoEventoToggleActiveView
)
from .views.public_views import ValidacionCertificadoView

app_name = 'certificado'

urlpatterns = [
    # Vistas principales de certificados
    path('crear/', CertificadoCreateView.as_view(), name='crear'),
    path('procesamiento/<int:pk>/status/', ProcesamientoStatusView.as_view(), name='procesamiento_status'),
    path('evento/<int:pk>/', EventoDetailView.as_view(), name='evento_detail'),
    path('lista/', CertificadoListView.as_view(), name='lista'),
    
    # Direcciones CRUD
    path('direcciones/', DireccionListView.as_view(), name='direccion_list'),
    path('direcciones/crear/', DireccionCreateView.as_view(), name='direccion_create'),
    path('direcciones/<int:pk>/', DireccionDetailView.as_view(), name='direccion_detail'),
    path('direcciones/<int:pk>/editar/', DireccionUpdateView.as_view(), name='direccion_edit'),
    path('direcciones/<int:pk>/eliminar/', DireccionDeleteView.as_view(), name='direccion_delete'),
    path('direcciones/<int:pk>/toggle-active/', DireccionToggleActiveView.as_view(), name='direccion_toggle_active'),
    
    # Plantillas CRUD
    path('plantillas/', PlantillaListView.as_view(), name='plantilla_list'),
    path('plantillas/crear/', PlantillaCreateView.as_view(), name='plantilla_create'),
    path('plantillas/<int:pk>/', PlantillaDetailView.as_view(), name='plantilla_detail'),
    path('plantillas/<int:pk>/editar/', PlantillaUpdateView.as_view(), name='plantilla_edit'),
    path('plantillas/<int:pk>/eliminar/', PlantillaDeleteView.as_view(), name='plantilla_delete'),
    
    # Catálogos CRUD
    # Modalidad
    path('modalidades/', ModalidadListView.as_view(), name='modalidad_list'),
    path('modalidades/crear/', ModalidadCreateView.as_view(), name='modalidad_create'),
    path('modalidades/<int:pk>/editar/', ModalidadUpdateView.as_view(), name='modalidad_edit'),
    path('modalidades/<int:pk>/eliminar/', ModalidadDeleteView.as_view(), name='modalidad_delete'),
    path('modalidades/<int:pk>/toggle-active/', ModalidadToggleActiveView.as_view(), name='modalidad_toggle_active'),
    
    # Tipo
    path('tipos/', TipoListView.as_view(), name='tipo_list'),
    path('tipos/crear/', TipoCreateView.as_view(), name='tipo_create'),
    path('tipos/<int:pk>/editar/', TipoUpdateView.as_view(), name='tipo_edit'),
    path('tipos/<int:pk>/eliminar/', TipoDeleteView.as_view(), name='tipo_delete'),
    path('tipos/<int:pk>/toggle-active/', TipoToggleActiveView.as_view(), name='tipo_toggle_active'),
    
    # TipoEvento
    path('tipos-evento/', TipoEventoListView.as_view(), name='tipo_evento_list'),
    path('tipos-evento/crear/', TipoEventoCreateView.as_view(), name='tipo_evento_create'),
    path('tipos-evento/<int:pk>/editar/', TipoEventoUpdateView.as_view(), name='tipo_evento_edit'),
    path('tipos-evento/<int:pk>/eliminar/', TipoEventoDeleteView.as_view(), name='tipo_evento_delete'),
    path('tipos-evento/<int:pk>/toggle-active/', TipoEventoToggleActiveView.as_view(), name='tipo_evento_toggle_active'),
    
    path('api/variantes/<int:direccion_id>/', get_variantes_api, name='get_variantes'),
    path('api/plantillas/<int:direccion_id>/', get_plantillas_api, name='get_plantillas'),
    path('api/preview-certificado/', CertificadoPreviewView.as_view(), name='preview_certificado'),
]
