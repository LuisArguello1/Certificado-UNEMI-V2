from django.urls import reverse

class MenuService:
    """
    Servicio para generar la estructura del menú lateral (Sidebar).
    Centraliza la definición de items y el cálculo de estado activo.
    """
    @staticmethod
    def get_menu_items(current_path, user):
        """
        Retorna la lista de items del menú filtrada por permisos.
        """
        
        # Helper para verificar si el usuario tiene CUALQUIER permiso de acceso al sistema
        # Si tiene modificar, obviamente puede leer.
        has_basic_access = user.is_authenticated and (
            user.is_superuser or 
            getattr(user, 'is_only_read', False) or 
            getattr(user, 'can_modify', False) or 
            getattr(user, 'can_delete', False) or 
            getattr(user, 'can_send_email', False)
        )

        try:
            dashboard_url = reverse('core:dashboard')
        except:
            dashboard_url = '#'

        menu = []
        
        # =====================================================================
        # DASHBOARD (Visible para todos los que entran al sistema)
        # =====================================================================
        menu.append({
            'name': 'Dashboard',
            'icon': 'chart-line',
            'url': dashboard_url,
            'active': current_path == dashboard_url
        })
        
        if not has_basic_access:
            return menu

        # =====================================================================
        # CERTIFICADOS
        # =====================================================================
        menu.append({'separator': True, 'label': 'CERTIFICADOS'})
        
        try:
            certificado_crear_url = reverse('certificado:crear')
            certificado_lista_url = reverse('certificado:lista')
            certificado_plantilla_url = reverse('certificado:plantilla_list')
            certificado_direccion_url = reverse('certificado:direccion_list')
            modalidad_url = reverse('certificado:modalidad_list')
            tipo_url = reverse('certificado:tipo_list')
            tipo_evento_url = reverse('certificado:tipo_evento_list')
        except:
            certificado_crear_url = '#'
            certificado_lista_url = '#'
            certificado_plantilla_url = '#'
            certificado_direccion_url = '#'
            modalidad_url = '#'
            tipo_url = '#'
            tipo_evento_url = '#'
        
        # Historial (Siempre visible para lectura)
        menu.append({
            'name': 'Historial',
            'icon': 'list-check',
            'url': certificado_lista_url,
            'active': (current_path == certificado_lista_url or current_path.startswith('/certificados/lista'))
        })

        # Generar Certificados: Solo si puede modificar (Staff/Superuser o flag can_modify)
        can_modify = getattr(user, 'can_modify', False) or user.is_staff or user.is_superuser
        if can_modify:
            menu.append({
                'name': 'Generar Certificados',
                'icon': 'file-signature',
                'url': certificado_crear_url,
                'active': current_path == certificado_crear_url
            })
        
        # =====================================================================
        # PLANTILLAS
        # =====================================================================
        menu.append({'separator': True, 'label': 'PLANTILLAS'})
        
        menu.append({
            'name': 'Plantillas',
            'icon': 'file-word',
            'url': certificado_plantilla_url,
            'active': 'plantillas' in current_path
        })
        
        menu.append({
            'name': 'Direcciones',
            'icon': 'building',
            'url': certificado_direccion_url,
            'active': 'direcciones' in current_path
        })

        # =====================================================================
        # CATÁLOGOS
        # =====================================================================
        menu.append({'separator': True, 'label': 'CATÁLOGOS'})

        menu.append({
            'name': 'Modalidades',
            'icon': 'tag',
            'url': modalidad_url,
            'active': 'modalidades' in current_path
        })

        menu.append({
            'name': 'Tipos Generales',
            'icon': 'tags',
            'url': tipo_url,
            'active': 'tipos/' in current_path and 'evento' not in current_path
        })

        menu.append({
            'name': 'Tipos de Evento',
            'icon': 'calendar-check',
            'url': tipo_evento_url,
            'active': 'tipos-evento' in current_path
        })
        
        # =====================================================================
        # ADMINISTRACIÓN (Solo Superuser/Staff con acceso a usuarios)
        # =====================================================================
        if user and (user.is_staff or user.is_superuser):
            menu.append({'separator': True, 'label': 'ADMINISTRACIÓN'})
            
            try:
                users_url = reverse('accounts:user_list')
            except:
                users_url = '#'
            
            menu.append({
                'name': 'Usuarios',
                'icon': 'users',
                'url': users_url,
                'active': current_path == users_url
            })

        return menu
