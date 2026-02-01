from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.conf import settings
from apps.certificado.models import Evento, Certificado, Estudiante, EmailDailyLimit

class DashboardService:
    """
    Servicio para centralizar la lógica de negocio del Dashboard.
    Sigue el patrón de 'Thin Views'.
    """

    @staticmethod
    def get_general_stats():
        """Calcula estadísticas generales y KPIs (Globales)."""
        qs_eventos = Evento.objects.all()
        
        return {
            'total_eventos': qs_eventos.count(),
            # 'mis_eventos_count' se elimina o se iguala al total si es necesario por compatibilidad, 
            'total_certificados': Certificado.objects.count(),
            'estudiantes_total': Estudiante.objects.count(),
            'certs_completados': Certificado.objects.filter(estado='completed').count(),
            'certs_pendientes': Certificado.objects.filter(estado='pending').count(),
            'certs_fallidos': Certificado.objects.filter(estado='failed').count(),
        }

    @staticmethod
    def get_recent_activity(limit=5):
        """Obtiene los últimos eventos creados (Global)."""
        return Evento.objects.all().order_by('-created_at')[:limit]

    @staticmethod
    def get_email_limit_status():
        """Obtiene el estado actual del límite de correos."""
        hoy = datetime.now().date()
        daily_limit = getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
        
        limit_record, _ = EmailDailyLimit.objects.get_or_create(date=hoy)
        correos_enviados_hoy = limit_record.count
        
        percent = 0
        if daily_limit > 0:
            percent = round((correos_enviados_hoy / daily_limit) * 100, 1)
            
        return {
            'limit': daily_limit,
            'sent': correos_enviados_hoy,
            'remaining': max(0, daily_limit - correos_enviados_hoy),
            'percent': percent
        }

    @staticmethod
    def get_chart_data(days=7):
        """Genera datos para los gráficos de Chart.js (últimos 7 días)."""
        hoy = datetime.now().date()
        last_n_days = [(hoy - timedelta(days=i)) for i in range(days-1, -1, -1)]
        chart_labels = [d.strftime("%Y-%m-%d") for d in last_n_days]
        start_date = last_n_days[0]
        end_date = last_n_days[-1]

        # 1. Correos Enviados
        email_limits = EmailDailyLimit.objects.filter(
            date__gte=start_date, 
            date__lte=end_date
        )
        email_map = {item.date.strftime("%Y-%m-%d"): item.count for item in email_limits}
        email_data = [email_map.get(label, 0) for label in chart_labels]

        # 2. Certificados Generados
        certs_qs = Certificado.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id'))
        
        cert_map = {item['date'].strftime("%Y-%m-%d"): item['count'] for item in certs_qs if item['date']}
        cert_data = [cert_map.get(label, 0) for label in chart_labels]

        return {
            'labels': chart_labels,
            'email_data': email_data,
            'cert_data': cert_data
        }
