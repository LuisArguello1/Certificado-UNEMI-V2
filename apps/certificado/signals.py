import os
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import PlantillaBase, VariantePlantilla, Certificado, Evento
from .services.google_drive_service import GoogleDriveService

logger = logging.getLogger(__name__)

# ... (upload_template_to_drive helper unchanged)

def delete_from_drive_by_name(name, parent_folder_name=None):
    """
    Helper para eliminar archivo/carpeta por nombre.
    """
    if not getattr(settings, 'GOOGLE_DRIVE_ENABLED', False):
        return

    try:
        drive_service = GoogleDriveService()
        root_folder_id = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        
        parent_id = root_folder_id
        if parent_folder_name:
            # Buscar ID del folder padre (ej: Plantillas_Base)
            found_parents = drive_service.find_items(parent_folder_name, parent_id=root_folder_id, mime_type='application/vnd.google-apps.folder')
            if found_parents:
                parent_id = found_parents[0]['id']
            else:
                logger.warning(f"Padre {parent_folder_name} no encontrado para borrar {name}")
                return

        # Buscar el item a borrar
        items = drive_service.find_items(name, parent_id=parent_id)
        for item in items:
            drive_service.delete_file(item['id'])
            
    except Exception as e:
        logger.error(f"Error eliminando {name} de Drive: {e}")

@receiver(post_save, sender=PlantillaBase)
def sync_plantilla_base_to_drive(sender, instance, created, **kwargs):
    if instance.archivo:
        upload_template_to_drive(instance.archivo, folder_name="Plantillas_Base")

@receiver(post_delete, sender=PlantillaBase)
def delete_plantilla_base_drive(sender, instance, **kwargs):
    """Elimina plantilla de Drive al borrar."""
    if instance.archivo:
        filename = os.path.basename(instance.archivo.name)
        delete_from_drive_by_name(filename, parent_folder_name="Plantillas_Base")

@receiver(post_save, sender=VariantePlantilla)
def sync_variante_plantilla_to_drive(sender, instance, created, **kwargs):
    if instance.archivo:
        upload_template_to_drive(instance.archivo, folder_name="Plantillas_Variantes")

@receiver(post_delete, sender=VariantePlantilla)
def delete_variante_plantilla_drive(sender, instance, **kwargs):
    """Elimina variante de Drive al borrar."""
    if instance.archivo:
        filename = os.path.basename(instance.archivo.name)
        delete_from_drive_by_name(filename, parent_folder_name="Plantillas_Variantes")

@receiver(post_delete, sender=Evento)
def delete_evento_drive(sender, instance, **kwargs):
    """Elimina carpeta completa del evento en Drive."""
    # La carpeta del evento se llama con su ID (str(instance.id))
    delete_from_drive_by_name(str(instance.id))

@receiver(post_delete, sender=Certificado)
def delete_certificado_drive(sender, instance, **kwargs):
    """Elimina carpeta/archivos del estudiante al borrar un certificado."""
    # En Drive, la estructura es EventoID -> EstudianteID -> certificado.pdf
    # Si borramos el certificado, borramos la carpeta del estudiante dentro del evento
    # OJO: Si el estudiante tiene múltiples certificados (raro pero posible?), esto borraría todo.
    # Asumimos 1 certificado por estudiante por evento.
    
    if not getattr(settings, 'GOOGLE_DRIVE_ENABLED', False):
        return

    try:
        drive_service = GoogleDriveService()
        root_folder_id = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        
        # 1. Encontrar carpeta Evento
        eventos = drive_service.find_items(str(instance.evento.id), parent_id=root_folder_id, mime_type='application/vnd.google-apps.folder')
        if not eventos:
            return
        
        evento_id_drive = eventos[0]['id']
        
        # 2. Encontrar carpeta Estudiante dentro de Evento
        # El modelo Certificado tiene instance.estudiante
        estudiante_id = str(instance.estudiante.id)
        
        estudiantes = drive_service.find_items(estudiante_id, parent_id=evento_id_drive, mime_type='application/vnd.google-apps.folder')
        
        for est_folder in estudiantes:
            drive_service.delete_file(est_folder['id'])
            logger.info(f"Carpeta estudiante {estudiante_id} eliminada de Drive.")
            
    except Exception as e:
        logger.error(f"Error eliminando certificado Drive para estudiante {instance.estudiante.id}: {e}")
