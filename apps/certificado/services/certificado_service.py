"""
Servicio principal para orquestar la generación masiva de certificados.

Este es el servicio de alto nivel que coordina todo el flujo.
"""

import logging
from typing import Dict, List
from django.db import transaction
from django.utils import timezone
from ..models import Evento, Estudiante, Certificado, ProcesamientoLote
from ..utils import parse_excel_estudiantes


logger = logging.getLogger(__name__)


class CertificadoService:
    """
    Servicio orquestador principal para generación masiva de certificados.
    
    Responsabilidades:
    - Crear registro de Evento
    - Parsear Excel
    - Crear registros de Estudiantes
    - Crear registros de Certificados (estado='pending')
    - Crear ProcesamientoLote
    - Encolar tareas Celery
    """
    
    @staticmethod
    @transaction.atomic
    def create_event_with_students(evento_data: Dict, excel_file, user, estudiantes_data=None) -> Evento:
        """
        Paso 1: Crea el Evento y los registros de Estudiantes (Nómina).
        No inicia procesamiento de certificados aún.
        """
        try:
            logger.info("Iniciando creación de evento y nómina")
            
            # 1. Parsear Excel o usar datos proporcionados
            if estudiantes_data is None:
                if excel_file is None:
                    raise ValueError("Se debe proporcionar un archivo Excel o datos de estudiantes")
                logger.info("Parseando archivo Excel...")
                estudiantes_data = parse_excel_estudiantes(excel_file)
            
            num_estudiantes = len(estudiantes_data)
            if num_estudiantes == 0:
                raise ValueError("El archivo Excel no contiene estudiantes")
            
            # 2. Crear Evento
            evento = Evento.objects.create(
                direccion=evento_data['direccion_gestion'],
                plantilla_seleccionada=evento_data.get('plantilla_seleccionada'),
                created_by=user,
                modalidad=evento_data['modalidad'],
                nombre_evento=evento_data['nombre_evento'],
                duracion_horas=evento_data['duracion_horas'],
                fecha_inicio=evento_data['fecha_inicio'],
                fecha_fin=evento_data['fecha_fin'],
                tipo=evento_data['tipo'],
                tipo_evento=evento_data['tipo_evento'],
                fecha_emision=evento_data['fecha_emision'],
                objetivo_programa=evento_data['objetivo_programa'],
                contenido_programa=evento_data['contenido_programa'],
            )
            
            # 3. Crear Estudiantes en bulk
            estudiantes_to_create = [
                Estudiante(
                    evento=evento,
                    nombres_completos=est_data['nombres_completos'],
                    correo_electronico=est_data['correo_electronico']
                )
                for est_data in estudiantes_data
            ]
            Estudiante.objects.bulk_create(estudiantes_to_create)
            
            logger.info(f"Evento {evento.id} creado con {num_estudiantes} estudiantes")
            return evento
            
        except Exception as e:
            logger.error(f"Error en create_event_with_students: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def initiate_generation_lote(evento_id: int) -> ProcesamientoLote:
        """
        Paso 2: Inicia la generación de certificados para un evento.
        Crea registros de Certificado 'pending' y encola tareas Celery.
        """
        from ..tasks import generate_certificate_task
        
        try:
            evento = Evento.objects.get(id=evento_id)
            estudiantes = Estudiante.objects.filter(evento=evento)
            num_estudiantes = estudiantes.count()
            
            if num_estudiantes == 0:
                raise ValueError("El evento no tiene estudiantes registrados")
                
            # 1. Crear/Actualizar Certificados y encolar tareas
            for estudiante in estudiantes:
                certificado, _ = Certificado.objects.get_or_create(
                    evento=evento,
                    estudiante=estudiante,
                    defaults={'estado': 'pending'}
                )
                
                # Si ya existía, resetear estado para que se procese
                if certificado.estado != 'pending':
                    certificado.estado = 'pending'
                    certificado.save()
                
                # Encolar tarea
                try:
                    generate_certificate_task.delay(certificado.id)
                except Exception as e:
                    logger.error(f"Error al encolar tarea para certificado {certificado.id}: {str(e)}")
                    raise

            
            # 2. Crear/Actualizar ProcesamientoLote
            lote, created = ProcesamientoLote.objects.get_or_create(
                evento=evento,
                defaults={
                    'total_estudiantes': num_estudiantes,
                    'estado': 'pending',
                    'fecha_inicio': timezone.now()
                }
            )
            
            if not created:
                lote.total_estudiantes = num_estudiantes
                lote.procesados = 0
                lote.exitosos = 0
                lote.fallidos = 0
                lote.estado = 'pending'
                lote.fecha_inicio = timezone.now()
                lote.fecha_fin = None
                lote.save()
            
            lote.estado = 'processing'
            lote.save()
            
            logger.info(f"Lote de generación iniciado para Evento {evento_id}")
            return lote
            
        except Exception as e:
            logger.error(f"Error en initiate_generation_lote: {str(e)}")
            raise

    @staticmethod
    def initiate_sending_lote(evento_id: int):
        """
        Paso 3: Encola el envío masivo de certificados ya generados.
        """
        from ..tasks import send_certificate_email_task
        from apps.certificado.models import EmailDailyLimit, Certificado
        
        try:
            evento = Evento.objects.get(id=evento_id)
            certificados = Certificado.objects.filter(
                evento=evento, 
                estado='completed',
                archivo_pdf__isnull=False
            )
            
            num_a_enviar = certificados.count()
            if num_a_enviar == 0:
                return 0, "No hay certificados listos para enviar."
                
            # Verificar límite
            puede_enviar, restantes, mensaje = EmailDailyLimit.puede_enviar_lote(num_a_enviar)
            if not puede_enviar:
                raise ValueError(mensaje)
            
            # IMPORTANTE: Cambiar estado masivamente a 'sending_email' ANTES de encolar
            # Esto asegura que la barra de progreso baje a 0% inmediatamente,
            # ya que 'completed' cuenta como finalizado en la lógica de progreso.
            cert_ids = list(certificados.values_list('id', flat=True))
            certificados.update(estado='sending_email', updated_at=timezone.now())
                
            for cert_id in cert_ids:
                send_certificate_email_task.delay(cert_id)
            
            # Asegurarse que el lote refleje que está procesando (emails)
            lote = ProcesamientoLote.objects.filter(evento=evento).first()
            if lote:
                lote.estado = 'processing'
                lote.save()
                
            return num_a_enviar, "Envío masivo encolado exitosamente."
            
        except Exception as e:
            logger.error(f"Error en initiate_sending_lote: {str(e)}", exc_info=True)
            raise e
