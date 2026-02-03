"""
Context processors para la app Core.

Los context processors añaden variables globales a todos los templates.
"""

from datetime import datetime
from apps.core.services.menu_service import MenuService


def global_context(request):
    """
    Añade variables globales a todos los templates.
    
    Variables disponibles:
    - app_name: Nombre de la aplicación
    - app_version: Versión del sistema
    - current_year: Año actual
    - menu_items: Items del menú lateral generados dinámicamente
    """
    return {
        'app_name': 'UNEMI - Certificados',
        'app_version': '1.0.0',
        'current_year': datetime.now().year,
        'menu_items': MenuService.get_menu_items(request.path, request.user),
    }
