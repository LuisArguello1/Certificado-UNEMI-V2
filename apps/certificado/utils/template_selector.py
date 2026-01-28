"""
Selector de plantillas de certificado.

Selecciona la plantilla apropiada basándose en el evento.
"""

import logging
from typing import Optional
from django.core.exceptions import ObjectDoesNotExist


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
    """
    
    @staticmethod
    def get_template_for_event(evento) -> str:
        """
        Obtiene la ruta del archivo de plantilla para un evento.
        
        Args:
            evento: Instancia del modelo Evento
        
        Returns:
            Ruta absoluta del archivo .docx de plantilla
        
        Raises:
            TemplateNotFoundError: Si no se encuentra plantilla válida
        
        Ejemplo:
            >>> from apps.certificado.utils.template_selector import TemplateSelector
            >>> evento = Evento.objects.get(id=1)
            >>> template_path = TemplateSelector.get_template_for_event(evento)
            >>> print(template_path)  # /path/to/media/plantillas_certificado/base/...
        """
        from ..models import PlantillaBase
        
        # Caso 1: Si hay variante seleccionada, usar esa
        if evento.plantilla_seleccionada and evento.plantilla_seleccionada.activo:
            if evento.plantilla_seleccionada.archivo:
                return evento.plantilla_seleccionada.archivo.path
            else:
                logger.warning(
                    f"Variante {evento.plantilla_seleccionada.id} no tiene archivo. "
                    f"Fallback a plantilla base."
                )
        
        # Caso 2: Usar plantilla base de la dirección
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
            
            return plantilla_base.archivo.path
            
        except ObjectDoesNotExist:
            raise TemplateNotFoundError(
                f"No existe una plantilla base activa para la dirección '{evento.direccion}'. "
                f"Por favor, configure una plantilla en el admin."
            )
        except Exception as e:
            logger.error(f"Error al obtener plantilla para evento {evento.id}: {str(e)}")
            raise TemplateNotFoundError(f"Error al obtener plantilla: {str(e)}")
    
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
    Función helper para obtener ruta de plantilla.
    
    Args:
        evento: Instancia del modelo Evento
    
    Returns:
        Ruta absoluta del archivo .docx
    
    Raises:
        TemplateNotFoundError: Si no hay plantilla válida
    """
    return TemplateSelector.get_template_for_event(evento)
