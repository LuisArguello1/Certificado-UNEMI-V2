import os
import logging
from datetime import datetime
from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from apps.certificado.models import Certificado, EmailDailyLimit

logger = logging.getLogger(__name__)

class EmailService:
    """
    Servicio responsable de construir y enviar correos electrónicos de certificados.
    """

    @staticmethod
    def send_certificate_email(certificado: Certificado) -> bool:
        """
        Envía el correo electrónico del certificado al estudiante.

        Args:
            certificado (Certificado): La instancia del certificado.

        Returns:
            bool: True si se envió correctamente, False en caso contrario.
        """
        try:
            # Actualizar estado
            certificado.estado = 'sending_email'
            certificado.save(update_fields=['estado', 'updated_at'])

            # Construir correo
            subject = f"Certificado - {certificado.evento.nombre_evento}"
            
            context = {
                'nombre_estudiante': certificado.estudiante.nombres_completos,
                'nombre_evento': certificado.evento.nombre_evento,
                'anio_actual': datetime.now().year,
            }

            html_content = render_to_string('certificado/email/certificado_email.html', context)
            
            text_content = EmailService._get_fallback_text_content(certificado)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[certificado.estudiante.correo_electronico]
            )

            email.attach_alternative(html_content, "text/html")

            # Adjuntar Logo
            EmailService._attach_logo(email)

            # Adjuntar PDF
            EmailService._attach_pdf(email, certificado)

            # Enviar
            email.send(fail_silently=False)

            # Actualizar límite diario y estado del certificado
            EmailDailyLimit.increment_count()
            
            certificado.estado = 'sent'
            certificado.enviado_email = True
            certificado.fecha_envio = timezone.now()
            certificado.intentos_envio += 1
            certificado.save()
            
            return True

        except Exception as e:
            logger.error(f"[EmailService] Error enviando email para certificado {certificado.id}: {str(e)}")
            certificado.intentos_envio += 1
            certificado.error_mensaje = f"Error en envío de email: {str(e)}"
            certificado.save()
            raise e

    @staticmethod
    def _get_fallback_text_content(certificado: Certificado) -> str:
        """Retorna el contenido de texto plano como respaldo para el correo."""
        return f"""
            Estimado/a {certificado.estudiante.nombres_completos},

            Nos complace comunicarle que, en reconocimiento a su valiosa participación en la Jornada: {certificado.evento.nombre_evento}, le hacemos llegar adjunto a este mensaje su certificado. Este documento acredita su activa intervención y compromiso durante la actividad desarrollada.

            Le invitamos a seguir formando parte de nuestras próximas actividades. Para más información, no dude en contactarnos.

            Saludos cordiales,
            Universidad Estatal de Milagro - UNEMI

            Todos los derechos reservados © UNEMI {datetime.now().year}
        """.strip()

    @staticmethod
    def _attach_logo(email: EmailMultiAlternatives):
        """Adjunta el logo institucional como imagen en línea si está disponible."""
        try:
            base_dir = str(settings.BASE_DIR)
            logo_path = os.path.join(base_dir, 'static', 'img', 'Unemi_correo.png')
            
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    logo_image = MIMEImage(logo_data)
                    logo_image.add_header('Content-ID', '<unemi_logo>')
                    logo_image.add_header('Content-Disposition', 'inline', filename='Unemi_correo.png')
                    email.attach(logo_image)
        except Exception as e:
            logger.warning(f"No se pudo adjuntar el logo: {str(e)}")

    @staticmethod
    def _attach_pdf(email: EmailMultiAlternatives, certificado: Certificado):
        """Adjunta el PDF del certificado al correo."""
        if not certificado.archivo_pdf:
             raise ValueError("El certificado no tiene archivo PDF generado")

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
