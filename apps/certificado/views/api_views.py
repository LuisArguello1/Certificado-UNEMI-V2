"""
API Views para el módulo de certificados.

Este módulo contiene endpoints JSON utilizados por las interfaces dinámicas
(AJAX) para la selección de plantillas y variantes.
"""

import logging
from django.http import JsonResponse
from apps.certificado.models import VariantePlantilla, PlantillaBase

logger = logging.getLogger(__name__)


def get_variantes_api(request, direccion_id):
    """
    API endpoint para obtener variantes de plantilla por dirección.
    Usado por AJAX en el formulario.
    
    Args:
        request: HttpRequest
        direccion_id: ID de la dirección
    
    Returns:
        JsonResponse con variantes disponibles
    """
    try:
        variantes = VariantePlantilla.objects.filter(
            plantilla_base__direccion_id=direccion_id,
            plantilla_base__es_activa=True,
            activo=True
        ).select_related('plantilla_base').order_by('orden', 'nombre')
        
        variantes_data = [
            {
                'id': v.id,
                'nombre': v.nombre,
                'descripcion': v.descripcion
            }
            for v in variantes
        ]
        
        return JsonResponse({
            'success': True,
            'variantes': variantes_data
        })
        
    except Exception as e:
        logger.error(f"Error al obtener variantes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_plantillas_api(request, direccion_id):
    """
    API endpoint para obtener plantilla base y sus variantes por dirección.
    Usado para el modal de selección de plantillas.
    
    Args:
        request: HttpRequest
        direccion_id: ID de la dirección
    
    Returns:
        JsonResponse con:
        - plantilla_base: {id, nombre}
        - variantes: [{id, nombre, descripcion}]
    """
    try:
        # Buscar plantilla base activa para la dirección
        plantilla_base = PlantillaBase.objects.filter(
            direccion_id=direccion_id,
            es_activa=True
        ).first()
        
        if not plantilla_base:
            return JsonResponse({
                'success': True,
                'plantilla_base': None,
                'variantes': []
            })
            
        # Buscar variantes activas
        variantes = VariantePlantilla.objects.filter(
            plantilla_base=plantilla_base,
            activo=True
        ).order_by('orden', 'nombre')
        
        variantes_data = [
            {
                'id': v.id,
                'nombre': v.nombre,
                'descripcion': v.descripcion
            }
            for v in variantes
        ]
        
        return JsonResponse({
            'success': True,
            'plantilla_base': {
                'id': plantilla_base.id,
                'nombre': plantilla_base.nombre,
                'descripcion': plantilla_base.descripcion
            },
            'variantes': variantes_data
        })
        
    except Exception as e:
        logger.error(f"Error al obtener plantillas: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
