from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from ..forms.auth_forms import CustomAuthenticationForm

from django.conf import settings
from axes.models import AccessAttempt
from axes.helpers import get_client_ip_address
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

class CustomLoginView(LoginView):
    """
    Vista de Login personalizada.
    """
    template_name = 'accounts/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Iniciar Sesión'
        return context

    def form_invalid(self, form):
        """
        Sobrescribimos para añadir mensaje de intentos restantes y tiempo de bloqueo.
        """
        response = super().form_invalid(form)
        
        username = form.cleaned_data.get('username')
        if username:
            # Buscar intentos fallidos para este usuario (solo username, no IP)
            attempts = AccessAttempt.objects.filter(
                username=username
            ).first()
            
            if attempts:
                failures = attempts.failures_since_start
                limit = getattr(settings, 'AXES_FAILURE_LIMIT', 5)
                remaining = limit - failures
                
                # Verificar si el cooloff ha expirado
                cooloff_time = getattr(settings, 'AXES_COOLOFF_TIME', timedelta(minutes=15))
                if isinstance(cooloff_time, (int, float)):
                    cooloff_time = timedelta(hours=cooloff_time)
                
                time_since_attempt = timezone.now() - attempts.attempt_time
                
                # Si el cooloff ha expirado, el usuario puede intentar de nuevo
                # (axes limpiará el registro automáticamente en el próximo intento)
                if time_since_attempt >= cooloff_time:
                    # El bloqueo ya expiró, este es un nuevo intento
                    messages.error(self.request, f"⚠️ Credenciales incorrectas.")
                elif remaining > 0:
                    # Todavía tiene intentos
                    messages.error(self.request, f"⚠️ Credenciales incorrectas. Le quedan {remaining} intentos antes del bloqueo temporal de 15 minutos.")
                else:
                    # Bloqueado - calcular tiempo restante
                    time_remaining = cooloff_time - time_since_attempt
                    minutes_remaining = int(time_remaining.total_seconds() / 60)
                    seconds_remaining = int(time_remaining.total_seconds() % 60)
                    
                    if minutes_remaining > 0:
                        time_str = f"{minutes_remaining} minutos"
                        if seconds_remaining > 0:
                            time_str += f" y {seconds_remaining} segundos"
                    else:
                        time_str = f"{seconds_remaining} segundos"
                    
                    messages.error(self.request, f"🔒 Su cuenta está bloqueada temporalmente. Tiempo restante: {time_str}. También puede contactar al administrador para ser desbloqueado.")
                 
        return response

class CustomLogoutView(LogoutView):
    """
    Vista de Logout.
    """
    next_page = reverse_lazy('accounts:login')
