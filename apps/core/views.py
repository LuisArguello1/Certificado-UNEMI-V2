"""
Views para la app Core.

Siguiendo arquitectura de views delgadas:
- Views solo coordinan services y renderización
- Lógica de negocio en services
- Contexto claro y bien estructurado
"""
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista principal del dashboard.
    
    Muestra métricas del sistema, archivos recientes y actividad.
    View delgada: obtiene datos del service y renderiza.
    """
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Menu items para el sidebar (Usando Service)
        from apps.core.services.menu_service import MenuService
        context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        
        # Breadcrumbs
        context['breadcrumbs'] = [
            {'name': 'Dashboard'}
        ]
        
        # Título de la página
        context['page_title'] = 'Dashboard'
        
        # Imports de modelos

        from apps.certificado.models import EmailDailyLimit
        from django.db.models import Count, Q, Sum
        from datetime import datetime, timedelta

        hoy = datetime.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio_mes = hoy.replace(day=1)

        # ===== LÍMITE DIARIO DE CORREOS =====
        from django.conf import settings
        daily_limit = getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
        
        limit_record, _ = EmailDailyLimit.objects.get_or_create(date=hoy)
        correos_enviados_hoy = limit_record.count
        
        context['email_daily_limit'] = daily_limit
        context['email_sent_today'] = correos_enviados_hoy
        context['email_remaining_today'] = max(0, daily_limit - correos_enviados_hoy)
        
        if daily_limit > 0:
            context['email_daily_percent'] = round((correos_enviados_hoy / daily_limit) * 100, 1)
        else:
            context['email_daily_percent'] = 0
        
        return context

