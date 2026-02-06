"""
Tareas Celery para generación y envío de certificados.

Este módulo define todas las tareas asíncronas del sistema, delegando la lógica
de negocio a los servicios correspondientes para mantener un código limpio y mantenible.
"""

import logging
import os
import time
from typing import Dict, Any, List

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

# Models
from apps.certificado.models import Certificado, ProcesamientoLote

# Services
from apps.certificado.services import (
    CertificateStorageService,
    EmailService,
    PDFConversionService,
    TemplateService,
)
from apps.certificado.services.qr_service import QRService 
from apps.certificado.utils import get_template_path

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

STATUS_GENERATING = 'generating'
STATUS_COMPLETED = 'completed'
STATUS_FAILED = 'failed'
STATUS_SENDING_EMAIL = 'sending_email'
STATUS_SENT = 'sent'

# Calculamos el rate limit al inicio
try:
    _rate_seconds = getattr(settings, 'EMAIL_RATE_LIMIT_SECONDS', 2)
    _emails_per_minute = 60 // max(1, _rate_seconds)
    RATE_LIMIT_VALUE = f"{_emails_per_minute}/m"
except Exception:
    RATE_LIMIT_VALUE = '30/m'


# =============================================================================
# TASKS
# =============================================================================

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='apps.certificado.tasks.generate_certificate_batch_task'
)
def generate_certificate_batch_task(self, certificado_ids: List[int]) -> Dict[str, Any]:
    """
    Tarea OPTIMIZADA: Procesa un lote de certificados (Batch Processing).
    
    Flujo:
    1. Genera todos los DOCX del lote.
    2. Ejecuta UNA SOLA instancia de LibreOffice para convertir todos a PDF.
    3. Finaliza cada uno (QR, Guardado, Estado).
    
    Esto reduce drásticamente el tiempo de startup de LibreOffice (4s -> 0.2s/cert).
    """
    logger.debug(f"Iniciando batch task para {len(certificado_ids)} certificados")
    
    certificados = Certificado.objects.select_related(
        'estudiante', 'estudiante__evento', 'estudiante__evento__direccion'
    ).filter(id__in=certificado_ids)
    
    # Mapas para seguimiento
    certs_map = {c.id: c for c in certificados}
    temp_docx_map = {} # {cert_id: path_docx}
    temp_pdf_map = {}  # {cert_id: path_pdf}
    temp_template_paths = set()  # Plantillas temporales descargadas de Azure
    docx_paths_list = []
    final_errors = []
    
    # Mapa de plantillas por evento (para evitar descargas repetidas)
    evento_template_map = {}  # {evento_id: template_path}
    
    try:
        # Puesto que vamos a procesar, marcamos todos como generating
        Certificado.objects.filter(id__in=certificado_ids).update(
            estado=STATUS_GENERATING, 
            updated_at=timezone.now()
        )
        
        # 1. Generación masiva de DOCX
        
        for cert in certificados:
            try:
                evento_id = cert.evento.id
                
                # Descargar plantilla solo si no la tenemos ya para este evento
                if evento_id not in evento_template_map:
                    template_path = get_template_path(cert.evento)
                    evento_template_map[evento_id] = template_path
                    temp_template_paths.add(template_path)
                else:
                    template_path = evento_template_map[evento_id]
                    logger.debug(f"Reutilizando plantilla para evento {evento_id}")
                
                variables = TemplateService.get_variables_from_evento_estudiante(
                    cert.evento, cert.estudiante
                )
                
                temp_docx = CertificateStorageService.get_temp_path(
                    f'cert_{cert.id}_{cert.estudiante.id}.docx'
                )
                
                TemplateService.generate_docx(template_path, variables, temp_docx)
                
                temp_docx_map[cert.id] = temp_docx
                docx_paths_list.append(temp_docx)
                
            except Exception as e:
                msg = f"Error generando DOCX para cert {cert.id}: {e}"
                logger.error(msg)
                final_errors.append(msg)
                _fail_certificate(cert, msg)

        # 2. Conversión BATCH a PDF
        if docx_paths_list:
            try:
                # Esta es la llamada mágica que optimiza todo
                # Retorna mapa {docx_path: pdf_path}
                conversion_results = PDFConversionService.convert_batch_docx_to_pdf(docx_paths_list)
                
                # Mapear resultados de vuelta a certificados
                for cert_id, docx_path in temp_docx_map.items():
                    if docx_path in conversion_results:
                        temp_pdf_map[cert_id] = conversion_results[docx_path]
                    else:
                        if cert_id in certs_map: # (Si no falló en paso 1)
                            msg = "Fallo en conversión PDF batch"
                            _fail_certificate(certs_map[cert_id], msg)
                            
            except Exception as e:
                # Si falla el batch completo, fallamos todos los pendientes
                logger.error(f"Fallo crítico en batch conversion: {e}")
                for cert_id in temp_docx_map.keys():
                    if cert_id in certs_map:
                        _fail_certificate(certs_map[cert_id], f"Error Batch PDF: {e}")

        # 3. Finalización Individual (QR + Guardado)
        for cert_id, pdf_path in temp_pdf_map.items():
            cert = certs_map.get(cert_id)
            if not cert: continue
            
            try:
                # QR
                if cert.evento.incluir_qr:
                    QRService.stamp_qr_on_pdf(pdf_path, cert.uuid_validacion)
                
                # Guardado final (ahora sube a Azure automáticamente)
                final_path = CertificateStorageService.save_pdf_only(
                    evento_id=cert.evento.id,
                    estudiante_id=cert.estudiante.id,
                    pdf_source_path=pdf_path,
                    nombres_estudiante=cert.estudiante.nombres_completos
                )
                
                # Éxito
                cert.archivo_pdf = final_path
                cert.estado = STATUS_COMPLETED
                cert.error_mensaje = ''
                cert.save()
                
            except Exception as e:
                logger.error(f"Error finalizando cert {cert.id}: {e}")
                _fail_certificate(cert, f"Error guardado/QR: {e}")

        # Actualizar progreso del evento (una sola vez al final del batch)
        if certificados:
            _update_batch_progress_sync(certificados[0].evento.id)

        return {
            'status': 'batch_completed',
            'processed': len(certificado_ids),
            'success': len(temp_pdf_map),
            'errors': len(final_errors)
        }

    except Exception as exc:
        logger.error(f"Error crítico en task batch: {exc}")
        raise self.retry(exc=exc, countdown=60)

    finally:
        # Limpieza masiva de archivos temporales
        # 1. (OPTIMIZACIÓN) NO BORRAR PLANTILLAS - Se reutilizan desde caché
        # for template_path in temp_template_paths:
        #     _safe_remove(template_path)
        
        # 2. DOCXs generados
        for path in docx_paths_list:
            _safe_remove(path)
        
        # 3. PDFs convertidos
        for path in temp_pdf_map.values():
            _safe_remove(path)


def _fail_certificate(cert, message):
    """Helper para marcar fallo individual."""
    try:
        cert.estado = STATUS_FAILED
        cert.error_mensaje = str(message)[:255]
        cert.save()
    except:
        pass

def _safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except:
        pass


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='apps.certificado.tasks.generate_certificate_task'
)
def generate_certificate_task(self, certificado_id: int) -> Dict[str, Any]:
    """
    Tarea Legacy: Mantenida por compatibilidad, pero envuelve la lógica batch.
    Procesa un solo certificado delegando a la tarea batch.
    """
    return generate_certificate_batch_task([certificado_id])


@shared_task(
    bind=True, 
    max_retries=5, 
    rate_limit=RATE_LIMIT_VALUE, 
    name='apps.certificado.tasks.send_certificate_email_task'
)
def send_certificate_email_task(self, certificado_id: int) -> Dict[str, Any]:
    """
    Tarea de envío de email con certificado PDF adjunto.
    Delega la lógica de construcción y envío al servicio EmailService.
    """
    certificado = None

    try:
        certificado = Certificado.objects.select_related(
            'estudiante', 'estudiante__evento'
        ).get(id=certificado_id)
        
        # Validación previa
        if not certificado.archivo_pdf:
             raise ValueError("El certificado no tiene archivo PDF generado")

        # Delegar envío a EmailService
        EmailService.send_certificate_email(certificado)

        # Actualizar progreso
        _update_batch_progress_sync(certificado.evento.id)

        return {
            'status': 'success',
            'certificado_id': certificado_id,
            'email': certificado.estudiante.correo_electronico
        }

    except Exception as exc:
        logger.error(f"[Email {certificado_id}] Error: {str(exc)}")
        
        if self.request.retries < self.max_retries:
             raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            if certificado:
                certificado.estado = STATUS_FAILED
                certificado.save()
                _update_batch_progress_sync(certificado.evento.id)
            
            return {
                'status': 'error',
                'certificado_id': certificado_id,
                'error': f"Max retries alcanzado: {str(exc)}"
            }


@shared_task(name='apps.certificado.tasks.update_batch_progress_task')
def update_batch_progress_task(evento_id: int) -> Dict[str, Any]:
    """
    Tarea Celery (wrapper) para actualizar el progreso.
    """
    success = _update_batch_progress_sync(evento_id)
    return {'status': 'success' if success else 'throttled', 'evento_id': evento_id}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _update_batch_progress_sync(evento_id: int) -> bool:
    """
    Actualiza el progreso del procesamiento en lote de forma SINCRÓNICA.
    Se utiliza cache para throttling y evitar saturar la base de datos.
    """
    cache_key = f"batch_progress_throttle_{evento_id}"
    
    last_update_time = cache.get(cache_key)
    current_time = time.time()
    
    # Throttle: 0.5 segundos
    if last_update_time is None or (current_time - last_update_time) >= 0.5:
        try:
            lote = ProcesamientoLote.objects.get(evento_id=evento_id)
            lote.actualizar_contadores()
            
            cache.set(cache_key, current_time, timeout=300)
            
            logger.info(f"[Lote {evento_id}] Progreso actualizado: {lote.porcentaje_progreso}%")
            return True
            
        except Exception as exc:
            logger.error(f"[Lote Evento {evento_id}] Error actualizando progreso: {str(exc)}")
            return False
            
    return False
