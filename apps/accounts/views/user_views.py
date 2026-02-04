from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from ..forms.user_forms import CustomUserCreationForm, CustomUserChangeForm
import logging

User = get_user_model()

logger = logging.getLogger(__name__)

class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.is_staff)

class UserListView(LoginRequiredMixin, SuperUserRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 10
    ordering = ['username']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestión de Usuarios'
        # Pasar un formulario vacío para el modal de creación
        context['create_form'] = CustomUserCreationForm()
        return context

class UserCreateView(LoginRequiredMixin, SuperUserRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_form.html' # Fallback para no-AJAX
    success_url = reverse_lazy('accounts:user_list')
    
    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return ['accounts/partials/user_form_fields.html']
        return [self.template_name]

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            messages.success(self.request, "Usuario creado correctamente.")
            return JsonResponse({
                'success': True,
                'message': 'Usuario creado correctamente.',
                'redirect_url': str(self.success_url)
            })
        messages.success(self.request, "Usuario creado correctamente.")
        return response
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Retornar el formulario con errores para que se muestre en el modal
            messages.error(self.request, "Por favor, corrige los errores en el formulario.")
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)

class UserUpdateView(LoginRequiredMixin, SuperUserRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'accounts/user_form.html' # Fallback
    success_url = reverse_lazy('accounts:user_list')
    
    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return ['accounts/partials/user_form_fields.html']
        return [self.template_name]

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            messages.success(self.request, "Usuario actualizado correctamente.")
            return JsonResponse({
                'success': True,
                'message': 'Usuario actualizado correctamente.',
                'redirect_url': str(self.success_url)
            })
        messages.success(self.request, "Usuario actualizado correctamente.")
        return response
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Retornar el formulario con errores para que se muestre en el modal
            messages.error(self.request, "Por favor, corrige los errores en el formulario.")
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)

class UserToggleActiveView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    """
    Vista para activar/desactivar un usuario mediante AJAX.
    """
    def post(self, request, pk):
        try:
            user = get_object_or_404(User, pk=pk)
            
            # No permitir desactivar el propio usuario
            if user == request.user:
                return JsonResponse({
                    'success': False,
                    'error': 'No puedes desactivar tu propia cuenta.'
                }, status=400)
            
            # Cambiar el estado
            user.is_active = not user.is_active
            user.save()
            
            logger.info(f"Usuario {user.username} {'activado' if user.is_active else 'desactivado'} por {request.user.username}")
            
            messages.success(request, f"Usuario {'activado' if user.is_active else 'desactivado'} correctamente.")
            return JsonResponse({
                'success': True,
                'is_active': user.is_active,
                'message': f"Usuario {'activado' if user.is_active else 'desactivado'} correctamente."
            })
            
        except Exception as e:
            logger.error(f"Error al cambiar estado de usuario {pk}: {str(e)}")
            messages.error(request, 'Error al cambiar el estado del usuario.')
            return JsonResponse({
                'success': False,
                'error': 'Error al cambiar el estado del usuario.'
            }, status=500)

from axes.utils import reset

class UserUnlockView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    """
    Vista para desbloquear (resetear intentos de login) un usuario manualmente.
    """
    def post(self, request, pk):
        try:
            user = get_object_or_404(User, pk=pk)
            
            # Resetear intentos en Axes
            # axes.utils.reset puede tomar username o ip. Aquí usamos username.
            # Nota: reset() devuelve count de accesos eliminados.
            count = reset(username=user.username)
            
            logger.info(f"Usuario {user.username} desbloqueado (Axes reset) por {request.user.username}. Registros eliminados: {count}")
            
            messages.success(request, f"Bloqueo de seguridad eliminado para {user.username}.")
            return JsonResponse({
                'success': True,
                'message': f"Bloqueo eliminado correctamente."
            })
            
        except Exception as e:
            logger.error(f"Error al desbloquear usuario {pk}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error al intentar desbloquear el usuario.'
            }, status=500)

class UserPasswordChangeView(LoginRequiredMixin, SuperUserRequiredMixin, UpdateView):
    """
    Vista AJAX para que un administrador cambie la contraseña de un usuario.
    """
    model = User
    form_class = SetPasswordForm
    template_name = 'accounts/partials/password_change_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.object
        # SetPasswordForm no recibe instance, solo user
        if 'instance' in kwargs:
            del kwargs['instance']
        return kwargs

    def form_valid(self, form):
        form.save()
        logger.info(f"Contraseña de usuario {self.object.username} cambiada por {self.request.user.username}")
        return JsonResponse({
            'success': True,
            'message': f'Contraseña de {self.object.username} actualizada correctamente.'
        })

    def form_invalid(self, form):
        return JsonResponse({
            'success': False,
            'errors': form.errors.get_json_data()
        }, status=400)

class UserDeleteView(LoginRequiredMixin, SuperUserRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Usuario eliminado correctamente.")
        return super().delete(request, *args, **kwargs)

    # Permitir borrar via POST directo desde el modal de la lista
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)
