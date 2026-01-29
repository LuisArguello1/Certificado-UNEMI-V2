"""
Tareas Celery para generación y envío de certificados.

Este módulo define todas las tareas asíncronas del sistema.
"""

import os
import logging
import time
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name='apps.certificado.tasks.generate_certificate_task')
def generate_certificate_task(self, certificado_id: int):
    """
    Tarea: Genera DOCX y convierte a PDF.
    NO envía email automáticamente.
    """
    from .models import Certificado
    from .services import TemplateService, PDFConversionService, CertificateStorageService
    from .utils import get_template_path
    
    certificado = None
    
    try:
        # Cargar certificado
        certificado = Certificado.objects.select_related(
            'evento', 'estudiante', 'evento__direccion'
        ).get(id=certificado_id)
        
        # Actualizar estado
        certificado.estado = 'generating'
        certificado.save(update_fields=['estado', 'updated_at'])
        
        # Obtener plantilla
        template_path = get_template_path(certificado.evento)
        
        # Construir variables
        variables = TemplateService.get_variables_from_evento_estudiante(
            certificado.evento,
            certificado.estudiante
        )
        
        # Generar DOCX temporal (necesario para conversión a PDF)
        temp_docx = CertificateStorageService.get_temp_path(
            f'cert_{certificado_id}_{certificado.estudiante.id}.docx'
        )
        
        # Generar DOCX temporal
        TemplateService.generate_docx(template_path, variables, temp_docx)
        
        # Convertir directamente a PDF
        temp_pdf = PDFConversionService.convert_docx_to_pdf(temp_docx)
        
        # Guardar SOLO el PDF en ubicación final
        pdf_path = CertificateStorageService.save_pdf_only(
            evento_id=certificado.evento.id,
            estudiante_id=certificado.estudiante.id,
            pdf_source_path=temp_pdf
        )
        
        # Actualizar certificado con ruta del PDF
        certificado.archivo_pdf = pdf_path
        certificado.estado = 'completed'
        certificado.error_mensaje = ''
        certificado.save()
        
        # Actualizar progreso del lote de forma sincrónica
        # Ejecutamos sincrónicamente para que el cambio se vea reflejado en DB 
        # inmediatamente después de completar el certificado.
        _update_batch_progress_sync(certificado.evento.id)
        
        # Limpiar archivos temporales
        try:
            if os.path.exists(temp_docx):
                os.remove(temp_docx)
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
        except:
            pass
        
        return {
            'status': 'success',
            'certificado_id': certificado_id,
            'estudiante': certificado.estudiante.nombres_completos
        }
        
    except Exception as exc:
        logger.error(f"[Certificado {certificado_id}] Error: {str(exc)}")
        if certificado:
            certificado.estado = 'failed'
            certificado.error_mensaje = f"Error en generación: {str(exc)}"
            certificado.save()
            # Actualizar progreso en caso de error
            _update_batch_progress_sync(certificado.evento.id)
        
        if 'timeout' in str(exc).lower() or 'temporary' in str(exc).lower():
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {'status': 'error', 'certificado_id': certificado_id, 'error': str(exc)}


@shared_task(bind=True, max_retries=5, rate_limit='30/m', name='apps.certificado.tasks.send_certificate_email_task')
def send_certificate_email_task(self, certificado_id: int):
    """
    Tarea de envío de email con certificado PDF adjunto.
    
    Args:
        certificado_id: ID del certificado a enviar
    
    Rate limit:
        30 emails por minuto (configurado en decorator)
    
    Retry:
        - Max 5 intentos
        - Delay exponencial: 60s, 120s, 300s, 600s, 1200s
    """
    from .models import Certificado
    
    certificado = None
    
    try:
        # Cargar certificado
        certificado = Certificado.objects.select_related(
            'evento', 'estudiante'
        ).get(id=certificado_id)
        
        # Verificar que existe el PDF
        if not certificado.archivo_pdf:
            raise ValueError("El certificado no tiene archivo PDF generado")
        
        # Actualizar estado
        certificado.estado = 'sending_email'
        certificado.save(update_fields=['estado', 'updated_at'])
        
        # Construir email con template HTML
        from django.template.loader import render_to_string
        from datetime import datetime
        import base64
        
        subject = f"Certificado - {certificado.evento.nombre_evento}"
        
        # Contexto para el template
        context = {
            'nombre_estudiante': certificado.estudiante.nombres_completos,
            'nombre_evento': certificado.evento.nombre_evento,
            'anio_actual': datetime.now().year,
        }
        
        # Renderizar template HTML
        html_content = render_to_string('certificado/email/certificado_email.html', context)
        
        # Versión texto plano como fallback
        text_content = f"""
Estimado/a {certificado.estudiante.nombres_completos},

Nos complace comunicarle que, en reconocimiento a su valiosa participación en la Jornada: {certificado.evento.nombre_evento}, le hacemos llegar adjunto a este mensaje su certificado. Este documento acredita su activa intervención y compromiso durante la actividad desarrollada.

Le invitamos a seguir formando parte de nuestras próximas actividades. Para más información, no dude en contactarnos.

Saludos cordiales,
Universidad Estatal de Milagro - UNEMI

Todos los derechos reservados © UNEMI {datetime.now().year}
        """.strip()
        
        # Crear email con alternativas (texto y HTML)
        from django.core.mail import EmailMultiAlternatives
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[certificado.estudiante.correo_electronico]
        )
        
        # Adjuntar versión HTML
        email.attach_alternative(html_content, "text/html")
        
        # LOGO: Usar CID (Content-ID) para máxima compatibilidad
        try:
            base_dir = str(settings.BASE_DIR)
            logo_path = os.path.join(base_dir, 'static', 'img', 'Unemi_correo.png')
            
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    
                    # Crear imagen MIME
                    from email.mime.image import MIMEImage
                    logo_image = MIMEImage(logo_data)
                    
                    # Definir Content-ID EXACTAMENTE como se usa en el HTML
                    logo_image.add_header('Content-ID', '<unemi_logo>')
                    logo_image.add_header('Content-Disposition', 'inline', filename='Unemi_correo.png')
                    
                    # Adjuntar al root del mensaje (o related)
                    email.attach(logo_image)
        except Exception:
            # Si falla el logo, el correo se envía igual sin él (fallback texto en HTML)
            pass
        
        # Adjuntar PDF del certificado
        
        # Adjuntar PDF del certificado
        pdf_path = certificado.archivo_pdf.path if hasattr(certificado.archivo_pdf, 'path') else certificado.archivo_pdf
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as pdf_file:
                email.attach(
                    filename=f'Certificado_{certificado.estudiante.nombres_completos.replace(" ", "_")}.pdf',
                    content=pdf_file.read(),
                    mimetype='application/pdf'
                )
        else:
            raise FileNotFoundError(f"Archivo PDF no encontrado: {pdf_path}")
        
        # Enviar email
        email.send(fail_silently=False)
        
        # Incrementar contador diario de emails
        from apps.certificado.models import EmailDailyLimit
        EmailDailyLimit.increment_count()
        
        # Actualizar certificado
        certificado.estado = 'sent'
        certificado.enviado_email = True
        certificado.fecha_envio = timezone.now()
        certificado.intentos_envio += 1
        certificado.save()
        
        # Actualizar progreso sincrónico cada vez que se envía uno
        _update_batch_progress_sync(certificado.evento.id)
        
        return {
            'status': 'success',
            'certificado_id': certificado_id,
            'email': certificado.estudiante.correo_electronico
        }
        
    except Exception as exc:
        logger.error(f"[Email {certificado_id}] Error: {str(exc)}")
        
        # Actualizar intentos
        if certificado:
            certificado.intentos_envio += 1
            certificado.error_mensaje = f"Error en envío de email: {str(exc)}"
            certificado.save()
        
        # Retry
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            # Max retries alcanzado, marcar como fallido
            if certificado:
                certificado.estado = 'failed'
                certificado.save()
                _update_batch_progress_sync(certificado.evento.id)
            
            return {
                'status': 'error',
                'certificado_id': certificado_id,
                'error': f"Max retries alcanzado: {str(exc)}"
            }


def _update_batch_progress_sync(evento_id: int):
    """
    Actualiza el progreso del procesamiento en lote de forma SINCRÓNICA.
    Se llama desde dentro de otras tareas para evitar el delay de la cola de Celery.
    """
    from .models import ProcesamientoLote
    
    # Key de throttling para no saturar la DB si hay muchos workers terminando a la vez
    cache_key = f"batch_progress_throttle_{evento_id}"
    
    # Verificar si podemos actualizar (throttling reducido a 0.5s para fluidez)
    last_update_time = cache.get(cache_key)
    current_time = time.time()
    
    # Si han pasado más de 0.5 segundos desde la última actualización, procesamos
    if last_update_time is None or (current_time - last_update_time) >= 0.5:
        try:
            lote = ProcesamientoLote.objects.get(evento_id=evento_id)
            lote.actualizar_contadores()
            
            # Actualizar timestamp de última actualización
            cache.set(cache_key, current_time, timeout=300)
            
            logger.info(f"[Lote {evento_id}] Progreso actualizado sincrónicamente: {lote.porcentaje_progreso}%")
            return True
            
        except Exception as exc:
            logger.error(f"[Lote Evento {evento_id}] Error actualizando progreso: {str(exc)}")
            return False
    return False


@shared_task(name='apps.certificado.tasks.update_batch_progress_task')
def update_batch_progress_task(evento_id: int):
    """
    Tarea Celery (wrapper) para actualizar el progreso.
    """
    success = _update_batch_progress_sync(evento_id)
    return {'status': 'success' if success else 'throttled', 'evento_id': evento_id}

