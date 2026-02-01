"""
Inicialización del paquete de vistas.
"""

from .certificado_views import (
    CertificadoCreateView,
    ProcesamientoStatusView,
    EventoDetailView,
    CertificadoListView,
    CertificadoPreviewView
)
from .api_views import get_variantes_api, get_plantillas_api
from .plantilla_views import (
    PlantillaListView,
    PlantillaDetailView,
    PlantillaCreateView,
    PlantillaUpdateView,
    PlantillaDeleteView
)
from .direccion_views import (
    DireccionListView,
    DireccionDetailView,
    DireccionCreateView,
    DireccionUpdateView,
    DireccionDeleteView
)

__all__ = [
    'CertificadoCreateView',
    'ProcesamientoStatusView',
    'EventoDetailView',
    'CertificadoListView',
    'CertificadoPreviewView',
    'get_variantes_api',
    'PlantillaListView',
    'PlantillaDetailView',
    'PlantillaCreateView',
    'PlantillaUpdateView',
    'PlantillaDeleteView',
    'DireccionListView',
    'DireccionDetailView',
    'DireccionCreateView',
    'DireccionUpdateView',
    'DireccionDeleteView',
]
