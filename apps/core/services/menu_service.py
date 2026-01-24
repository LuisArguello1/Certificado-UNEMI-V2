from django.urls import reverse

class MenuService:
    """
    Servicio para generar la estructura del menú lateral (Sidebar).
    Centraliza la definición de items y el cálculo de estado activo.
    """
    
    @staticmethod
    def get_menu_items(current_path, user=None):
        """
        Retorna la lista de items del menú filtrada por permisos.
        """
        
        try:
            dashboard_url = reverse('core:dashboard')
        except:
            dashboard_url = '#'

        menu = []
        
        # Dashboard siempre visible
        menu.append({
            'name': 'Dashboard',
            'icon': 'tachometer-alt',
            'url': dashboard_url,
            'active': current_path == dashboard_url
        })
        
        # Sección de Correo
        menu.append({'separator': True, 'label': 'ENVIOS MASIVOS'})
        
        try:
            correo_list_url = reverse('correo:list')
            correo_create_url = reverse('correo:create')
        except:
            correo_list_url = '#'
            correo_create_url = '#'
        
        menu.append({
            'name': 'Historial',
            'icon': 'history',
            'url': correo_list_url,
            # Active si está en lista o detalle, pero no en crear
            'active': (current_path == correo_list_url or 
                      (current_path.startswith('/correo/') and current_path != correo_create_url))
        })
        
        menu.append({
            'name': 'Nueva Campaña',
            'icon': 'paper-plane',
            'url': correo_create_url,
            'active': current_path == correo_create_url
        })
        
        # Sección de Sistema
        menu.append({'separator': True, 'label': 'CURSOS'})
        
        return menu
