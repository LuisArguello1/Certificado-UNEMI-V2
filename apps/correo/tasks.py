"""
Tareas de Celery para procesamiento asíncrono de envío de correos masivos.
"""
from celery import shared_task
from django.conf import settings
from django.core.mail import get_connection
from django.utils import timezone
import time
import logging
import re
try:
    from text_unidecode import unidecode
except ImportError:
    try:
        from unidecode import unidecode
    except ImportError:
        def unidecode(text): return text

logger = logging.getLogger(__name__)


def validate_and_normalize_email(email):
    if not email: return None
    try:
        email = unidecode(email).strip().lower()
    except Exception:
        email = email.strip().lower()
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return None
    return email


def check_daily_limit():
    from .models import EmailDailyLimit
    return EmailDailyLimit.can_send_email(), EmailDailyLimit.get_remaining_today()


@shared_task(bind=True, name='apps.correo.tasks.send_campaign_async')
def send_campaign_async(self, campaign_id):
    """
    Tarea MONOLÍTICA robusta para envío de campañas.
    Maneja todo el proceso en una sola ejecución para evitar problemas de tareas hijas en Windows.
    """
    from .models import EmailCampaign, EmailRecipient, EmailDailyLimit
    from .services import EmailCampaignService
    
    logger.info(f"[Celery] Iniciando envío de campaña {campaign_id}")
    
    try:
        # 1. Inicialización
        campaign = EmailCampaign.objects.get(id=campaign_id)
        campaign.status = 'processing'
        campaign.celery_task_id = self.request.id
        campaign.save()
        
        # Configuración
        rate_limit = getattr(settings, 'EMAIL_RATE_LIMIT_SECONDS', 2)
        batch_size = getattr(settings, 'EMAIL_BATCH_SIZE', 10)
        
        # Destinatarios pendientes
        recipients = campaign.recipients.filter(status='pending')
        total_recipients = recipients.count()
        
        if total_recipients == 0:
            campaign.status = 'completed'
            campaign.save()
            return "Sin destinatarios pendientes"

        # 2. Bucle de Envío
        sent_count = 0
        failed_count = 0
        
        # Abrir conexión
        connection = get_connection()
        connection.open()
        
        try:
            # Iterar sobre TODOS los pendientes (Django QuerySet es lazy, está bien)
            for i, recipient in enumerate(recipients):
                
                # --- Control de Pausas por Lote (Cada 10 correos) ---
                if i > 0 and i % batch_size == 0:
                    # Actualizar progreso en BD cada lote
                    campaign.current_batch = (i // batch_size) + 1
                    campaign.update_statistics()
                    
                    # Recalcular % progreso
                    total = campaign.total_recipients
                    processed = campaign.sent_count + campaign.failed_count
                    if total > 0:
                        campaign.progress = int((processed / total) * 100)
                    campaign.save()
                    
                    # Pequeña pausa extra entre lotes para respirar
                    logger.info(f"[Celery] Lote completado. Pausando 1s...")
                    time.sleep(1)

                # --- Verificación Diario ---
                can_send, _ = check_daily_limit()
                if not can_send:
                    logger.warning("[Celery] Límite diario alcanzado. Deteniendo.")
                    recipient.error_message = 'Límite diario alcanzado'
                    recipient.save()
                    break # Salir del bucle

                # --- Envío Individual ---
                try:
                    # Validar
                    clean_email = validate_and_normalize_email(recipient.email)
                    if not clean_email:
                        raise ValueError("Email inválido")
                    
                    recipient.email = clean_email
                    
                    # Enviar
                    EmailCampaignService._send_email_to_recipient_with_connection(
                        campaign, recipient, connection
                    )
                    
                    # Éxito
                    recipient.status = 'sent'
                    recipient.sent_at = timezone.now()
                    recipient.error_message = ''
                    recipient.save()
                    
                    # Contadores
                    EmailDailyLimit.increment_count()
                    sent_count += 1
                    logger.info(f"[Celery] Enviado a {recipient.email}")
                    
                except Exception as e:
                    # Fallo
                    logger.error(f"[Celery] Fallo al enviar a {recipient.email}: {e}")
                    recipient.status = 'failed'
                    recipient.error_message = str(e)
                    recipient.save()
                    failed_count += 1

                # --- Rate Limiting (Pausa entre correos) ---
                time.sleep(rate_limit)
                
        finally:
            connection.close()

        # 3. Finalización
        campaign.update_statistics()
        
        # Si quedan pendientes (por límite diario), no marcar completed
        pending = campaign.recipients.filter(status='pending').count()
        if pending == 0:
            campaign.status = 'completed'
            campaign.progress = 100
        else:
            # Se detuvo antes de terminar
            campaign.status = 'completed' # O 'stopped' si prefieres
            logger.warning(f"[Celery] Campaña detenida con {pending} pendientes")

        campaign.sent_at = timezone.now()
        campaign.save()
        
        return f"Fin. Enviados: {sent_count}, Fallidos: {failed_count}"

    except Exception as e:
        logger.error(f"[Celery] Error CRÍTICO en tarea: {e}", exc_info=True)
        try:
            c = EmailCampaign.objects.get(id=campaign_id)
            c.status = 'failed'
            c.save()
        except: pass
        return f"Error: {e}"
