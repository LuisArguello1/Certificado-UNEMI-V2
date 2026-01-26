import os
import logging
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageService:
    """
    Servicio para gestionar la robustez del almacenamiento (NAS).
    Centraliza la detección de errores y verificación de disponibilidad.
    """

    @staticmethod
    def check_storage_health():
        """
        Verifica si el MEDIA_ROOT (NAS) está montado y es accesible.
        Retorna (bool, mensaje).
        """
        media_root = settings.MEDIA_ROOT
        
        try:
            if not os.path.exists(media_root):
                return False, f"El almacenamiento no es accesible en la ruta: {media_root}"
            
            # Intento de prueba de escritura/lectura mínima si es necesario
            # test_file = os.path.join(media_root, '.health_check')
            # with open(test_file, 'w') as f: f.write('ok')
            
            return True, "Almacenamiento conectado correctamente"
        except Exception as e:
            logger.error(f"Error crítico de almacenamiento: {str(e)}")
            return False, f"Error de comunicación con el NAS: {str(e)}"

    @staticmethod
    def get_file_status(file_field):
        """
        Verifica el estado de un archivo específico de un modelo.
        Evita errores 404/500 al intentar acceder a archivos que no existen en el NAS.
        """
        if not file_field or not hasattr(file_field, 'name') or not file_field.name:
            return {
                'exists': False,
                'path': None,
                'error': 'Campo de archivo está vacío'
            }
        
        try:
            # Primero verificar si el almacenamiento base es accesible
            is_online, _ = StorageService.check_storage_health()
            if not is_online:
                 return {
                    'exists': False,
                    'path': None,
                    'error': 'El almacenamiento NAS está fuera de línea'
                }

            exists = file_field.storage.exists(file_field.name)
            return {
                'exists': exists,
                'path': file_field.path if exists else None,
                'url': file_field.url if exists else None,
                'error': None if exists else 'Archivo no encontrado físicamente en el NAS'
            }
        except Exception as e:
            logger.warning(f"No se pudo verificar archivo en NAS: {str(e)}")
            return {
                'exists': False,
                'path': None,
                'error': f"Error de conexión con el NAS: {str(e)}"
            }

    @staticmethod
    def safe_get_path(file_field):
        """
        Retorna el path absoluto de forma segura, o None si no existe.
        """
        status = StorageService.get_file_status(file_field)
        return status['path'] if status['exists'] else None

    @staticmethod
    def ensure_directory(path):
        """
        Asegura que un directorio existe en el NAS.
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                return True
            return True
        except Exception as e:
            logger.error(f"No se pudo crear directorio en NAS: {str(e)}")
            return False
