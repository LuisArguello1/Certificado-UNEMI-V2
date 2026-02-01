"""
Context processors para la app Core.

Los context processors añaden variables globales a todos los templates.
Se ha optimizado para incluir caching en operaciones costosas como el chequeo de NAS.
"""

from datetime import datetime
from django.core.cache import cache
from apps.core.services.menu_service import MenuService
from apps.core.services.storage_service import StorageService

def global_context(request):
    """
    Añade variables globales a todos los templates.
    
    Variables disponibles:
    - app_name: Nombre de la aplicación
    - app_version: Versión del sistema
    - current_year: Año actual
    - menu_items: Items del menú lateral generados dinámicamente
    - storage_status: Estado de la conexión al NAS (cacheado)
    """
    
    # Cache key para el estado del almacenamiento
    CACHE_KEY_STORAGE = 'global_storage_health_status'
    CACHE_TIMEOUT = 60  # Cachear por 60 segundos
    
    # Intentar obtener del cache
    storage_data = cache.get(CACHE_KEY_STORAGE)
    
    if storage_data is None:
        # Verificar salud del NAS
        is_online, message = StorageService.check_storage_health()
        
        storage_data = {
            'is_online': is_online,
            'message': message
        }
        
        # Guardar en cache
        cache.set(CACHE_KEY_STORAGE, storage_data, CACHE_TIMEOUT)
    
    return {
        'app_name': 'UNEMI - Certificados',
        'app_version': '1.0.0',
        'current_year': datetime.now().year,
        'menu_items': MenuService.get_menu_items(request.path, request.user),
        'storage_status': storage_data
    }
