"""
Servicio para gestionar el envío masivo de correos.
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from ..models import EmailCampaign, EmailRecipient, Curso
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)


class EmailCampaignService:
    """
    Servicio para crear y enviar campañas de correo masivo.
    """
    
    @staticmethod
    def create_campaign_from_course(name, subject, message, course_id):
        """
        Crea una nueva campaña basada en los estudiantes de un curso.
        
        Args:
            name: Nombre de la campaña
            subject: Asunto del correo
            message: Mensaje personalizado
            course_id: ID del curso
            
        Returns:
            EmailCampaign: La campaña creada
        """
        try:
            course = Curso.objects.get(id=course_id)
        except Curso.DoesNotExist:
            raise ValueError("El curso seleccionado no existe.")

        estudiantes = course.estudiantes.all()
        if not estudiantes.exists():
            raise ValueError("El curso seleccionado no tiene estudiantes inscritos.")

        # Crear la campaña
        campaign = EmailCampaign.objects.create(
            name=name,
            subject=subject,
            message=message,
            course=course,
            total_recipients=estudiantes.count()
        )
        
        # Crear los destinatarios basados en los estudiantes del curso
        recipients = []
        for estudiante in estudiantes:
            # Generar link al portal público
            # Asumimos que la URL name es 'curso:portal' o similar
            # Sería ideal pasar el host, pero por ahora guardamos la ruta relativa o absoluta si tenemos request.
            # Mejor opción: Guardar solo la base y construir el link completo al enviar, 
            # O construir aquí un link genérico.
            # El requerimiento dice: "btn con un link hacia una pagina del mismo sistema"
            # Incluimos el curso_id para que el portal abra el modal automáticamente
            link = f"{reverse('curso:public_portal')}?curso_id={course.id}"
            
            recipient = EmailRecipient(
                campaign=campaign,
                full_name=estudiante.nombre_completo,
                email=estudiante.correo,
                certificate_link=link # Guardamos la ruta base
            )
            recipients.append(recipient)
        
        EmailRecipient.objects.bulk_create(recipients)
        
        return campaign
    
    @staticmethod
    def send_campaign(campaign_id):
        """
        Envía todos los correos de una campaña.
        Args:
            campaign_id: ID de la campaña
        """
        result = {
            'success': False,
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            campaign = EmailCampaign.objects.get(id=campaign_id)
            campaign.status = 'processing'
            campaign.save()
            
            # Obtener destinatarios pendientes
            recipients = campaign.recipients.filter(status='pending')
            
            for recipient in recipients:
                try:
                    # Enviar el correo
                    EmailCampaignService._send_email_to_recipient(campaign, recipient)
                    
                    # Actualizar estado
                    recipient.status = 'sent'
                    recipient.sent_at = timezone.now()
                    recipient.save()
                    
                    result['sent'] += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    recipient.status = 'failed'
                    recipient.error_message = error_msg
                    recipient.save()
                    
                    result['failed'] += 1
                    result['errors'].append(f"{recipient.email}: {error_msg}")
                    
                    logger.error(f"Error enviando correo a {recipient.email}: {error_msg}")
            
            # Actualizar estadísticas de la campaña
            campaign.update_statistics()
            campaign.status = 'completed'
            campaign.sent_at = timezone.now()
            campaign.save()
            
            result['success'] = True
            
        except EmailCampaign.DoesNotExist:
            result['errors'].append("Campaña no encontrada")
        except Exception as e:
            result['errors'].append(f"Error general: {str(e)}")
            logger.error(f"Error en campaña {campaign_id}: {str(e)}")
        
        return result
    
    @staticmethod
    def _send_email_to_recipient(campaign, recipient):
        """
        Envía un correo a un destinatario específico.
        """
        domain = getattr(settings, 'SITE_URL', 'http://localhost:8000') 
        full_link = f"{domain}{recipient.certificate_link}"

        context = {
            'full_name': recipient.full_name,
            'first_name': recipient.full_name.split()[0],
            'certificate_link': full_link,
            'custom_message': campaign.message, 
        }
        
        # 1. Renderizar HTML inicial
        html_content = render_to_string('correo/emails/certificate_email.html', context)
        
        # 2. Procesar imágenes Base64 -> CID
        from django.core.mail import EmailMultiAlternatives
        from email.mime.image import MIMEImage
        import re
        import base64
        
        # Regex para encontrar imágenes base64
        img_regex = r'<img[^>]+src="data:image/(?P<ext>png|jpeg|jpg|gif);base64,(?P<data>[^"]+)"[^>]*>'
        
        images_to_attach = []
        
        def replace_callback(match):
            ext = match.group('ext')
            data_str = match.group('data')
            
            # Generar Content-ID único
            import uuid
            content_id = str(uuid.uuid4())
            
            # Decodificar
            img_data = base64.b64decode(data_str)
            
            # --- RESIZING (Compactación) ---
            try:
                from PIL import Image
                import io
                
                image_stream = io.BytesIO(img_data)
                with Image.open(image_stream) as img_pil:
                    
                    # Definir ancho máximo estándar para emails (600px - 800px)
                    MAX_WIDTH = 600
                    
                    if img_pil.width > MAX_WIDTH:
                        # Calcular nueva altura manteniendo aspecto
                        ratio = MAX_WIDTH / float(img_pil.width)
                        new_height = int((float(img_pil.height) * float(ratio)))
                        
                        # Redimensionar (LANCZOS es alta calidad)
                        img_pil = img_pil.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
                        
                        # Guardar de nuevo a bytes
                        output_stream = io.BytesIO()
                        # Mantener formato original
                        format_str = 'JPEG' if ext.lower() == 'jpg' else ext.upper()
                        if format_str == 'JPG': format_str = 'JPEG'
                        
                        # Optimizar calidad
                        img_pil.save(output_stream, format=format_str, quality=85, optimize=True)
                        img_data = output_stream.getvalue()
                        
            except ImportError:
                # Si Pillow no está, usamos la original sin resize
                logger.warning("Pillow no instalado, omitiendo resize de imagen.")
            except Exception as e:
                logger.error(f"Error resize imagen: {e}")
                # Fallback a original si falla
                pass
            # -------------------------------
            
            # Crear objeto MIMEImage con la data (posiblemente redimensionada)
            img = MIMEImage(img_data)
            img.add_header('Content-ID', f'<{content_id}>')
            img.add_header('Content-Disposition', 'inline')
            images_to_attach.append(img)
            
            original_tag = match.group(0)
            # Reemplazar src y asegurar estilo responsivo
            # Forzamos max-width: 100% en estilo inline para clientes que lo soporten
            new_tag = original_tag.replace(f'data:image/{ext};base64,{data_str}', f'cid:{content_id}')
            
            # Inyectar style="max-width: 100%; height: auto;" si no existe ya
            if 'style="' not in new_tag:
                new_tag = new_tag.replace('<img ', '<img style="max-width: 100%; height: auto;" ')
            
            return new_tag

        # Ejecutar reemplazo
        final_html = re.sub(img_regex, replace_callback, html_content)
        
        # 3. Crear mensaje MultiAlternative
        plain_message = strip_tags(final_html)
        
        msg = EmailMultiAlternatives(
            subject=campaign.subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient.email]
        )
        msg.attach_alternative(final_html, "text/html")
        
        # 4. Adjuntar imágenes procesadas
        for img in images_to_attach:
            msg.attach(img)
            
        # 5. Enviar
        msg.send(fail_silently=False)
    
    @staticmethod
    def retry_failed_emails(campaign_id):
        # ... (Logica de retry igual que antes)
        result = {
            'success': False,
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            campaign = EmailCampaign.objects.get(id=campaign_id)
            failed_recipients = campaign.recipients.filter(status='failed')
            
            for recipient in failed_recipients:
                try:
                    recipient.status = 'pending'
                    recipient.error_message = ''
                    recipient.save()
                    
                    EmailCampaignService._send_email_to_recipient(campaign, recipient)
                    
                    recipient.status = 'sent'
                    recipient.sent_at = timezone.now()
                    recipient.save()
                    result['sent'] += 1
                    
                except Exception as e:
                    recipient.status = 'failed'
                    recipient.error_message = str(e)
                    recipient.save()
                    result['failed'] += 1
                    result['errors'].append(f"{recipient.email}: {str(e)}")
            
            campaign.update_statistics()
            campaign.save()
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Error: {str(e)}")
        
        return result
