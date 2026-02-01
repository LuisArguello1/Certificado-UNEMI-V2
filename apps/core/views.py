"""
Views para la app Core.

Siguiendo arquitectura de views delgadas:
- Views solo coordinan services y renderización
- Lógica de negocio en services
- Contexto claro y bien estructurado
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.services.dashboard_service import DashboardService

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista principal del dashboard.
    Refactorizada para usar DashboardService (Thin View).
    """
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 1. Breadcrumbs y UI
        context['breadcrumbs'] = [{'name': 'Dashboard'}]
        context['page_title'] = 'Dashboard'
        
        # 2. Obtener datos del servicio
        # 2. Obtener datos del servicio (Globales)
        stats = DashboardService.get_general_stats()
        recent_activity = DashboardService.get_recent_activity()
        email_status = DashboardService.get_email_limit_status()
        chart_data = DashboardService.get_chart_data()
        
        # 3. Inyectar en contexto
        context['stats'] = stats
        context['recent_eventos'] = recent_activity
        context['chart_data'] = chart_data
        
        # Mapeo de datos para el bloque de email (compatibilidad con template)
        context['email_daily_limit'] = email_status['limit']
        context['email_sent_today'] = email_status['sent']
        context['email_remaining_today'] = email_status['remaining']
        context['email_daily_percent'] = email_status['percent']
        
        return context
