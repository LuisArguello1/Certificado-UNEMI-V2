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
            'active': (current_path == correo_list_url or 
                      (current_path.startswith('/correo/') and current_path != correo_create_url))
        })
        
        menu.append({
            'name': 'Nueva Campaña',
            'icon': 'paper-plane',
            'url': correo_create_url,
            'active': current_path == correo_create_url
        })
        
        # Sección de Cursos
        menu.append({'separator': True, 'label': 'GESTIÓN DE CURSOS'})

        try:
            curso_list_url = reverse('curso:list')
            curso_create_url = reverse('curso:create')
            plantilla_list_url = reverse('curso:plantilla_list')
        except:
            curso_list_url = '#'
            curso_create_url = '#'
            plantilla_list_url = '#'

        menu.append({
            'name': 'Cursos',
            'icon': 'graduation-cap',
            'url': curso_list_url,
            'active': (current_path.startswith('/curso/') and 
                      'plantillas' not in current_path and 
                      current_path != curso_create_url)
        })

        menu.append({
            'name': 'Nuevo Curso',
            'icon': 'plus-circle',
            'url': curso_create_url,
            'active': current_path == curso_create_url
        })

        # Sección de Plantillas
        menu.append({
            'name': 'Plantillas',
            'icon': 'certificate',
            'url': plantilla_list_url,
            'active': 'plantillas' in current_path
        })
        
        return menu
