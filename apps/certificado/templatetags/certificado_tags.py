"""
Template tags personalizados para la aplicación de certificados.

Filtros:
    - get_item: Obtiene un valor de diccionario por clave
"""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Obtiene un elemento de un diccionario por clave.
    
    Uso en templates:
        {{ my_dict|get_item:key_variable }}
    
    Args:
        dictionary: Diccionario fuente
        key: Clave a buscar
    
    Returns:
        Valor del diccionario o None si no existe
    """
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)
