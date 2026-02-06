"""
Selector de plantillas de certificado.

Selecciona la plantilla apropiada basándose en el evento y descarga
el archivo desde el storage (local o Azure) a una ubicación temporal.
"""

import logging
import os
import tempfile
from typing import Optional
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage


logger = logging.getLogger(__name__)


class TemplateNotFoundError(Exception):
    """
    Error cuando no se encuentra una plantilla válida.
    """
    pass


class TemplateSelector:
    """
    Clase para seleccionar la plantilla apropiada para un evento.
    
    Lógica:
    1. Si el evento tiene plantilla_seleccionada (variante) → usar esa
    2. Si no, usar la plantilla base de la dirección
    3. Si no existe plantilla → lanzar error
    4. Descargar el archivo a ubicación temporal para procesamiento
    """
    
    @staticmethod
    def get_template_for_event(evento) -> str:
        """
        Obtiene la plantilla para un evento usando CACHÉ local.
        
        Args:
            evento: Instancia del modelo Evento
        
        Returns:
            Ruta absoluta del archivo .docx (puede estar hackeado o recién descargado)
        
        Raises:
            TemplateNotFoundError: Si no se encuentra plantilla válida
        """
        from ..models import PlantillaBase
        
        # Determinar qué archivo usar y construir un ID único para caché
        archivo_field = None
        cache_filename = None
        
        # Caso 1: Si hay variante seleccionada
        if evento.plantilla_seleccionada and evento.plantilla_seleccionada.activo:
            if evento.plantilla_seleccionada.archivo:
                archivo_field = evento.plantilla_seleccionada.archivo
                # Importante: usar el tiempo de modificación o hash si posible, 
                # pero por simplicidad usamos ID. Si cambia la plantilla,
                # el admin debería subir una nueva (o podemos limpiar caché).
                cache_filename = f"variante_{evento.plantilla_seleccionada.id}.docx"
            else:
                logger.warning(
                    f"Variante {evento.plantilla_seleccionada.id} no tiene archivo. "
                    f"Fallback a plantilla base."
                )
        
        # Caso 2: Usar plantilla base de la dirección
        if not archivo_field:
            try:
                plantilla_base = PlantillaBase.objects.get(
                    direccion=evento.direccion,
                    es_activa=True
                )
                
                if not plantilla_base.archivo:
                    raise TemplateNotFoundError(
                        f"La plantilla base para la dirección '{evento.direccion}' "
                        f"no tiene archivo asociado."
                    )
                
                archivo_field = plantilla_base.archivo
                cache_filename = f"base_{plantilla_base.id}.docx"
                
            except ObjectDoesNotExist:
                raise TemplateNotFoundError(
                    f"No existe una plantilla base activa para la dirección '{evento.direccion}'. "
                    f"Por favor, configure una plantilla en el admin."
                )
        
        # --- Lógica de Caché ---
        cache_dir = os.path.join(tempfile.gettempdir(), "unemi_templates_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        final_path = os.path.join(cache_dir, cache_filename)
        
        # Si ya existe en caché, retornarlo directamente
        if os.path.exists(final_path):
            # Opcional: Podríamos verificar tamaño > 0
            logger.debug(f"Usando plantilla en caché: {final_path}")
            return final_path

        # Si no existe, descargar
        try:
            logger.info(f"Descargando plantilla a caché: {final_path}")
            
            with open(final_path, 'wb') as temp_file:
                archivo_field.open('rb')
                temp_file.write(archivo_field.read())
                archivo_field.close()
            
            return final_path
            
        except Exception as e:
            # Si falla descarga y quedó archivo corrupto, intentar borrarlo
            if os.path.exists(final_path):
                try: os.remove(final_path)
                except: pass
                
            logger.error(f"Error al descargar plantilla evento {evento.id}: {str(e)}")
            raise TemplateNotFoundError(f"Error al descargar plantilla: {str(e)}")
    
    @staticmethod
    def get_template_object(evento):
        """
        Obtiene el objeto de plantilla (PlantillaBase o VariantePlantilla).
        
        Args:
            evento: Instancia del modelo Evento
        
        Returns:
            Objeto PlantillaBase o VariantePlantilla
        """
        from ..models import PlantillaBase
        
        if evento.plantilla_seleccionada and evento.plantilla_seleccionada.activo:
            return evento.plantilla_seleccionada
        
        try:
            return PlantillaBase.objects.get(
                direccion=evento.direccion,
                es_activa=True
            )
        except ObjectDoesNotExist:
            raise TemplateNotFoundError(
                f"No existe una plantilla activa para la dirección '{evento.direccion}'."
            )


def get_template_path(evento) -> str:
    """
    Función helper para obtener ruta de plantilla temporal.
    
    Args:
        evento: Instancia del modelo Evento
    
    Returns:
        Ruta absoluta del archivo .docx temporal
    
    Raises:
        TemplateNotFoundError: Si no hay plantilla válida
    
    IMPORTANTE: El archivo temporal debe ser eliminado después de su uso
    """
    return TemplateSelector.get_template_for_event(evento)

