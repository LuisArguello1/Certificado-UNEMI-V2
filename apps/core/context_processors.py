"""
Context processors para la app Core.

Los context processors añaden variables globales a todos los templates.
"""

from datetime import datetime
from apps.core.services.menu_service import MenuService


def global_context(request):
    """
    Añade variables globales a todos los templates.
    """
    user = request.user
    
    # El superusuario y el Staff siempre tienen todos los permisos
    is_admin = user.is_authenticated and (user.is_superuser or user.is_staff)
    
    perms_u = {
        'can_modify': user.is_authenticated and (getattr(user, 'can_modify', False) or is_admin),
        'can_delete': user.is_authenticated and (getattr(user, 'can_delete', False) or is_admin),
        'can_send_email': user.is_authenticated and (getattr(user, 'can_send_email', False) or is_admin),
        'is_only_read': user.is_authenticated and (getattr(user, 'is_only_read', False) and not is_admin),
    }

    return {
        'app_name': 'UNEMI - Certificados',
        'app_version': '1.0.0',
        'current_year': datetime.now().year,
        'menu_items': MenuService.get_menu_items(request.path, user),
        'perms_u': perms_u,
        'csp_nonce': getattr(request, 'csp_nonce', ''),
    }
