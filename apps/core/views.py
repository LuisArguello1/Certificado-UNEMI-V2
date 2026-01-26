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
        from apps.curso.models import Curso, Estudiante, Certificado
        from apps.correo.models import EmailCampaign, EmailRecipient
        from django.db.models import Count, Q, Sum
        from datetime import datetime, timedelta
        
        # ===== MÉTRICAS PRINCIPALES =====
        context['total_cursos'] = Curso.objects.filter(estado='disponible').count()
        context['total_estudiantes'] = Estudiante.objects.count()
        context['total_certificados'] = Certificado.objects.exclude(archivo_generado='').count()
        context['total_campañas'] = EmailCampaign.objects.count()
        
        # ===== DISTRIBUCIÓN DE CURSOS POR ESTADO =====
        cursos_por_estado = Curso.objects.values('estado').annotate(
            total=Count('id')
        ).order_by('-total')
        context['cursos_por_estado'] = list(cursos_por_estado)
        
        # ===== TOP 5 CURSOS CON MÁS ESTUDIANTES =====
        context['top_cursos'] = Curso.objects.annotate(
            num_estudiantes=Count('estudiantes')
        ).order_by('-num_estudiantes')[:5]
        
        # ===== ACTIVIDAD RECIENTE =====
        context['estudiantes_recientes'] = Estudiante.objects.select_related('curso').order_by('-fecha_registro')[:10]
        context['certificados_recientes'] = Certificado.objects.select_related(
            'estudiante', 'estudiante__curso'
        ).exclude(archivo_generado='').order_by('-fecha_generacion')[:5]
        
        # ===== ESTADÍSTICAS DE CORREO =====
        # Total de correos enviados vs fallidos
        total_enviados = EmailRecipient.objects.filter(status='sent').count()
        total_fallidos = EmailRecipient.objects.filter(status='failed').count()
        total_pendientes = EmailRecipient.objects.filter(status='pending').count()
        
        context['correos_enviados'] = total_enviados
        context['correos_fallidos'] = total_fallidos
        context['correos_pendientes'] = total_pendientes
        
        # Tasa de éxito de envíos
        total_procesados = total_enviados + total_fallidos
        if total_procesados > 0:
            context['tasa_exito_correos'] = round((total_enviados / total_procesados) * 100, 1)
        else:
            context['tasa_exito_correos'] = 0
        
        # Campañas recientes
        context['campañas_recientes'] = EmailCampaign.objects.select_related('course').order_by('-created_at')[:5]
        
        # Campañas activas (processing)
        context['campañas_activas'] = EmailCampaign.objects.filter(status='processing').count()
        
        # ===== MÉTRICAS TEMPORALES =====
        hoy = datetime.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio_mes = hoy.replace(day=1)
        
        # Certificados generados hoy/semana/mes
        context['certificados_hoy'] = Certificado.objects.filter(
            fecha_generacion__date=hoy
        ).count()
        context['certificados_semana'] = Certificado.objects.filter(
            fecha_generacion__date__gte=inicio_semana
        ).count()
        context['certificados_mes'] = Certificado.objects.filter(
            fecha_generacion__date__gte=inicio_mes
        ).count()
        
        # Tasa de generación de certificados
        if context['total_estudiantes'] > 0:
            context['tasa_certificacion'] = round(
                (context['total_certificados'] / context['total_estudiantes']) * 100, 1
            )
        else:
            context['tasa_certificacion'] = 0
        
        return context

