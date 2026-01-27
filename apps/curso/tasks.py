from celery import shared_task
from .models import Curso, Estudiante, Certificado
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='apps.curso.tasks.generate_course_certificates_async')
def generate_course_certificates_async(self, curso_id):
    """
    Genera certificados masivamente para un curso de forma asíncrona.
    Actualiza el progreso en el modelo Curso.
    """
    from .services.certificate_service import CertificateService
    
    try:
        curso = Curso.objects.get(id=curso_id)
        curso.generation_status = 'processing'
        curso.generation_task_id = self.request.id
        curso.generation_progress = 0
        curso.save()
        
        logger.info(f"[Celery] Iniciando generación de certificados para curso {curso.nombre} (ID: {curso_id})")
        
        # Obtener estudiantes
        # Optimizamos query
        estudiantes = Estudiante.objects.filter(curso=curso)
        total = estudiantes.count()
        
        if total == 0:
            curso.generation_status = 'completed'
            curso.generation_progress = 100
            curso.save()
            return "Sin estudiantes para procesar"
            
        processed = 0
        success_count = 0
        error_count = 0
        
        for estudiante in estudiantes:
            try:
                # Crear o actualizar registro de certificado
                certificado, created = Certificado.objects.update_or_create(
                    estudiante=estudiante,
                    defaults={'plantilla': curso.plantilla_certificado}
                )
                
                # Generar PDF (Operación pesada)
                result = CertificateService.generate_pdf(certificado)
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    logger.error(f"[Celery] Falló generación PDF para {estudiante.cedula}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"[Celery] Error procesando estudiante {estudiante.id}: {str(e)}")
            
            # Actualizar progreso
            processed += 1
            progress = int((processed / total) * 100)
            
            # Actualizar BD cada 5% o al final para no saturar
            if progress % 5 == 0 or processed == total:
                curso.generation_progress = progress
                curso.save(update_fields=['generation_progress'])
                
        # Finalización
        curso.generation_status = 'completed'
        curso.generation_progress = 100
        curso.save()
        
        logger.info(f"[Celery] Fin generación curso {curso_id}. Éxitos: {success_count}, Errores: {error_count}")
        return f"Generados: {success_count}, Errores: {error_count}"
        
    except Exception as e:
        logger.error(f"[Celery] Error CRÍTICO generando certificados curso {curso_id}: {str(e)}", exc_info=True)
        try:
            c = Curso.objects.get(id=curso_id)
            c.generation_status = 'failed'
            c.save()
        except: pass
        return f"Error crítico: {str(e)}"
