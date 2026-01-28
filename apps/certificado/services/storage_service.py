"""
Servicio de almacenamiento para archivos de certificados.

Organiza y guarda archivos DOCX y PDF en estructura de directorios.
"""

import os
import shutil
import logging
from django.conf import settings


logger = logging.getLogger(__name__)


class CertificateStorageService:
    """
    Servicio para organizar y almacenar archivos de certificados.
    
    Estructura de directorios:
        media/certificados/{evento_id}/{estudiante_id}/
            certificado.docx
            certificado.pdf
    """
    
    @staticmethod
    def get_certificate_directory(evento_id: int, estudiante_id: int) -> str:
        """
        Obtiene la ruta del directorio para un certificado.
        
        Args:
            evento_id: ID del evento
            estudiante_id: ID del estudiante
        
        Returns:
            Ruta absoluta del directorio
        """
        base_path = getattr(settings, 'CERTIFICADO_STORAGE_PATH', 
                           os.path.join(settings.MEDIA_ROOT, 'certificados'))
        cert_dir = os.path.join(base_path, str(evento_id), str(estudiante_id))
        return cert_dir
    
    @staticmethod
    def ensure_directory_exists(directory_path: str):
        """
        Asegura que existe un directorio, creándolo si es necesario.
        
        Args:
            directory_path: Ruta del directorio
        """
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
    
    @staticmethod
    def save_certificate_files(evento_id: int, estudiante_id: int,
                              docx_source_path: str, pdf_source_path: str) -> tuple:
        """
        Mueve y organiza los archivos de certificado en la estructura correcta.
        
        Args:
            evento_id: ID del evento
            estudiante_id: ID del estudiante
            docx_source_path: Ruta temporal del DOCX generado
            pdf_source_path: Ruta temporal del PDF generado
        
        Returns:
            Tupla (docx_relative_path, pdf_relative_path) para guardar en base de datos
        """
        try:
            # Obtener directorio destino
            dest_dir = CertificateStorageService.get_certificate_directory(evento_id, estudiante_id)
            CertificateStorageService.ensure_directory_exists(dest_dir)
            
            # Rutas de destino
            docx_dest = os.path.join(dest_dir, 'certificado.docx')
            pdf_dest = os.path.join(dest_dir, 'certificado.pdf')
            
            # Copiar archivos (no mover, para mantener originales si son necesarios)
            if os.path.exists(docx_source_path):
                shutil.copy2(docx_source_path, docx_dest)
            else:
                logger.warning(f"DOCX source no encontrado: {docx_source_path}")
            
            if os.path.exists(pdf_source_path):
                shutil.copy2(pdf_source_path, pdf_dest)
            else:
                logger.warning(f"PDF source no encontrado: {pdf_source_path}")
            
            # Convertir a rutas relativas para la base de datos
            media_root = settings.MEDIA_ROOT
            docx_relative = os.path.relpath(docx_dest, media_root).replace('\\', '/')
            pdf_relative = os.path.relpath(pdf_dest, media_root).replace('\\', '/')
            
            return docx_relative, pdf_relative
            
        except Exception as e:
            logger.error(f"Error al guardar archivos de certificado: {str(e)}")
            raise

    @staticmethod
    def save_pdf_only(evento_id: int, estudiante_id: int, pdf_source_path: str) -> str:
        """
        Guarda solo el archivo PDF en la estructura correcta.
        
        Args:
            evento_id: ID del evento
            estudiante_id: ID del estudiante
            pdf_source_path: Ruta temporal del PDF generado
        
        Returns:
            Ruta relativa del PDF para guardar en base de datos
        """
        try:
            # Obtener directorio destino
            dest_dir = CertificateStorageService.get_certificate_directory(evento_id, estudiante_id)
            CertificateStorageService.ensure_directory_exists(dest_dir)
            
            # Ruta de destino
            pdf_dest = os.path.join(dest_dir, 'certificado.pdf')
            
            # Copiar archivo
            if os.path.exists(pdf_source_path):
                shutil.copy2(pdf_source_path, pdf_dest)
            else:
                logger.warning(f"PDF source no encontrado: {pdf_source_path}")
                raise FileNotFoundError(f"PDF source no encontrado: {pdf_source_path}")
            
            # Convertir a ruta relativa para la base de datos
            media_root = settings.MEDIA_ROOT
            pdf_relative = os.path.relpath(pdf_dest, media_root).replace('\\', '/')
            
            return pdf_relative
            
        except Exception as e:
            logger.error(f"Error al guardar PDF: {str(e)}")
            raise
    
    @staticmethod
    def get_temp_path(filename: str) -> str:
        """
        Obtiene una ruta temporal para un archivo.
        
        Args:
            filename: Nombre del archivo
        
        Returns:
            Ruta absoluta en directorio temporal
        """
        import tempfile
        temp_dir = tempfile.gettempdir()
        return os.path.join(temp_dir, filename)
