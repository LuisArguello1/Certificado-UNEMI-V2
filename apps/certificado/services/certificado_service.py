"""
Servicio principal para orquestar la generación masiva de certificados.

Este servicio coordina el flujo completo: desde la creación del evento y 
carga de estudiantes, hasta la generación y envío de los certificados.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User

from ..models import Evento, Estudiante, Certificado, ProcesamientoLote, EmailDailyLimit
from ..utils import parse_excel_estudiantes

logger = logging.getLogger(__name__)


class CertificadoService:
    """
    Servicio orquestador principal para la gestión de eventos de certificación.
    
    Responsibilities:
        - Creación de eventos y nóminas (importación Excel).
        - Iniciación de generación masiva (PDFs).
        - Iniciación de envío masivo (Emails).
    """
    
    @staticmethod
    @transaction.atomic
    def create_event_with_students(
        evento_data: Dict[str, Any], 
        excel_file: Optional[Any], 
        user: User, 
        estudiantes_data: Optional[List[Dict[str, str]]] = None
    ) -> Evento:
        """
        Crea un Evento y su nómina de estudiantes asociada.

        Args:
            evento_data (Dict[str, Any]): Datos del formulario del evento.
            excel_file (Optional[Any]): Archivo Excel subido (request.FILES).
            user (User): Usuario que crea el evento.
            estudiantes_data (Optional[List[Dict]]): Datos de estudiantes ya procesados (opcional).

        Returns:
            Evento: La instancia del evento creado.

        Raises:
            ValueError: Si no se proveen datos de estudiantes válidos.
        """
        try:
            logger.info(f"Iniciando creación de evento por usuario: {user.username}")
            
            # 1. Preparar datos de estudiantes
            if not estudiantes_data:
                if not excel_file:
                    raise ValueError("Debe proporcionar un archivo Excel o datos de estudiantes.")
                
                logger.info("Parseando archivo Excel...")
                estudiantes_data = parse_excel_estudiantes(excel_file)
            
            num_estudiantes = len(estudiantes_data)
            if num_estudiantes == 0:
                raise ValueError("La lista de estudiantes está vacía.")
            
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
            
            # 3. Crear Estudiantes (Bulk Insert para eficiencia)
            estudiantes_objs = [
                Estudiante(
                    evento=evento,
                    nombres_completos=est['nombres_completos'],
                    correo_electronico=est['correo_electronico']
                )
                for est in estudiantes_data
            ]
            Estudiante.objects.bulk_create(estudiantes_objs)
            
            logger.info(f"Evento {evento.id} creado exitosamente con {num_estudiantes} estudiantes.")
            return evento
            
        except Exception as e:
            logger.error(f"Error creando evento: {e}", exc_info=True)
            raise

    @staticmethod
    def initiate_generation_lote(evento_id: int) -> ProcesamientoLote:
        """
        Inicia el proceso asíncrono de generación de certificados (PDFs).

        Crea los registros de certificado en estado 'pending' y el lote de procesamiento,
        luego encola las tareas individuales.

        Args:
            evento_id (int): ID del evento a procesar.

        Returns:
            ProcesamientoLote: El objeto de seguimiento del lote.
        """
        # Importación local para evitar dependencias circulares
        # Importación local para evitar dependencias circulares
        from ..tasks import generate_certificate_task, generate_certificate_batch_task
        
        
        try:
            evento = Evento.objects.get(id=evento_id)
            estudiantes = Estudiante.objects.filter(evento=evento)
            total = estudiantes.count()
            
            if total == 0:
                raise ValueError("El evento no tiene estudiantes registrados.")

            # 1. Preparar registros de Certificado
            certificado_ids = []
            
            # Usamos get_or_create para manejar reintentos sin duplicar
            for estudiante in estudiantes:
                cert, created = Certificado.objects.get_or_create(
                    evento=evento,
                    estudiante=estudiante,
                    defaults={'estado': 'pending'}
                )
                
                # Si ya existe (reintento), resetear a pending
                if not created and cert.estado != 'pending':
                    cert.estado = 'pending'
                    cert.error_mensaje = ''
                    cert.save(update_fields=['estado', 'error_mensaje'])
                
                certificado_ids.append(cert.id)

            # 2. Encolar tareas en LOTES (Chunking) optimization
            BATCH_SIZE = 20
            # Dividir lista de IDs en chunks de 20
            chunks = [certificado_ids[i:i + BATCH_SIZE] for i in range(0, len(certificado_ids), BATCH_SIZE)]
            
            logger.info(f"Encolando {len(chunks)} lotes de generación (Total: {len(certificado_ids)} certs)")
            
            for chunk_ids in chunks:
                generate_certificate_batch_task.delay(chunk_ids)

            # 3. Gestionar Lote de Procesamiento
            lote, created = ProcesamientoLote.objects.get_or_create(
                evento=evento,
                defaults={
                    'total_estudiantes': total,
                    'estado': 'pending',
                    'fecha_inicio': timezone.now()
                }
            )
            
            if not created:
                # Resetear lote existente
                lote.total_estudiantes = total
                lote.procesados = 0
                lote.exitosos = 0
                lote.fallidos = 0
                lote.estado = 'processing'
                lote.fecha_inicio = timezone.now()
                lote.fecha_fin = None
                lote.save()
            else:
                lote.estado = 'processing'
                lote.save()
            
            logger.info(f"Generación iniciada para evento {evento_id}. Lote {lote.id}.")
            return lote

        except Exception as e:
            logger.error(f"Error iniciando generación para evento {evento_id}: {e}", exc_info=True)
            raise

    @staticmethod
    def initiate_sending_lote(evento_id: int) -> Tuple[int, str]:
        """
        Inicia el envío masivo de certificados por correo electrónico.

        Verifica límites diarios, actualiza estados y encola tareas de envío.

        Args:
            evento_id (int): ID del evento.

        Returns:
            Tuple[int, str]: (Cantidad de envíos encolados, Mensaje de estado).
        """
        # Importación local para evitar dependencias circulares
        from ..tasks import send_certificate_email_task
        
        try:
            evento = Evento.objects.get(id=evento_id)
            
            # Buscar certificados listos para enviar
            # Deben estar 'completed' (generados) y tener archivo PDF
            certificados = Certificado.objects.filter(
                evento=evento, 
                estado='completed',
                archivo_pdf__isnull=False
            ).exclude(archivo_pdf='')
            
            count = certificados.count()
            if count == 0:
                return 0, "No hay certificados generados listos para enviar."
            
            # Verificar límite diario de correos
            permitido, _, mensaje_limite = EmailDailyLimit.puede_enviar_lote(count)
            if not permitido:
                raise ValueError(mensaje_limite)
            
            # Actualización masiva de estado a 'sending_email'
            # Esto bloquea reintentos inmediatos y actualiza la UI
            cert_ids = list(certificados.values_list('id', flat=True))
            certificados.update(
                estado='sending_email', 
                updated_at=timezone.now()
            )
            
            # Encolar tareas
            for cert_id in cert_ids:
                send_certificate_email_task.delay(cert_id)
            
            # Actualizar estado del lote si existe
            lote = ProcesamientoLote.objects.filter(evento=evento).first()
            if lote:
                lote.estado = 'processing'
                lote.save(update_fields=['estado'])
                
            logger.info(f"Envío iniciado para evento {evento_id}. {count} correos encolados.")
            return count, "Envío masivo encolado exitosamente."
            
        except Exception as e:
            logger.error(f"Error iniciando envío para evento {evento_id}: {e}", exc_info=True)
            raise
