"""
Servicio de almacenamiento para archivos de certificados.

Gestiona la organización física de archivos DOCX y PDF en el sistema de archivos,
siguiendo la estructura jerárquica por evento y estudiante.
"""

import os
import shutil
import logging
import tempfile
from typing import Tuple, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class CertificateStorageService:
    """
    Servicio para persistencia y organización de archivos generados.
    
    Patrón de almacenamiento:
        MEDIA_ROOT/certificados/{evento_id}/{estudiante_id}/{filename}
    """
    
    @staticmethod
    def get_certificate_directory(evento_id: int, estudiante_id: int) -> str:
        """
        Calcula la ruta absoluta del directorio de almacenamiento para un estudiante.

        Args:
            evento_id (int): ID del evento.
            estudiante_id (int): ID del estudiante.

        Returns:
            str: Ruta absoluta al directorio destino.
        """
        base_path = getattr(settings, 'CERTIFICADO_STORAGE_PATH', None)
        if not base_path:
            base_path = os.path.join(settings.MEDIA_ROOT, 'certificados')
            
        return os.path.join(base_path, str(evento_id), str(estudiante_id))
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """
        Crea el directorio si no existe (idempotente).
        
        Args:
            directory_path (str): Ruta absoluta.
        """
        os.makedirs(directory_path, exist_ok=True)
    
    @classmethod
    def save_certificate_files(
        cls, 
        evento_id: int, 
        estudiante_id: int,
        docx_source_path: str, 
        pdf_source_path: str
    ) -> Tuple[str, str]:
        """
        Almacena el par de archivos (DOCX, PDF) en su ubicación final.

        Copia los archivos desde su ubicación temporal a la estructura definitiva
        y retorna las rutas relativas para guardar en la BD.

        Args:
            evento_id (int): ID del evento.
            estudiante_id (int): ID del estudiante.
            docx_source_path (str): Ruta absoluta del DOCX temporal.
            pdf_source_path (str): Ruta absoluta del PDF temporal.

        Returns:
            Tuple[str, str]: (docx_relative_path, pdf_relative_path) relativas a MEDIA_ROOT.

        Raises:
            FileNotFoundError: Si los archivos fuente no existen.
            OSError: Si hay error de permisos o disco.
        """
        try:
            dest_dir = cls.get_certificate_directory(evento_id, estudiante_id)
            cls.ensure_directory_exists(dest_dir)
            
            # Definir destinos finales
            docx_dest = os.path.join(dest_dir, 'certificado.docx')
            pdf_dest = os.path.join(dest_dir, 'certificado.pdf')
            
            # Validar fuentes
            if not os.path.exists(docx_source_path):
                raise FileNotFoundError(f"Fuente DOCX no encontrada: {docx_source_path}")
            
            if not os.path.exists(pdf_source_path):
                # Logueamos warning pero no fallamos críticamente en DOCX,
                # Si falta PDF es crítico para el flujo.
                raise FileNotFoundError(f"Fuente PDF no encontrada: {pdf_source_path}")
            
            # Copiar archivos
            shutil.copy2(docx_source_path, docx_dest)
            shutil.copy2(pdf_source_path, pdf_dest)
            
            # Calcular rutas relativas para Django FileField
            media_root = str(settings.MEDIA_ROOT)
            
            # Relpath maneja correctamente los separadores de sistema
            docx_rel = os.path.relpath(docx_dest, media_root)
            pdf_rel = os.path.relpath(pdf_dest, media_root)
            
            # Normalizar a slash para BD (Django convention)
            return (docx_rel.replace('\\', '/'), pdf_rel.replace('\\', '/'))
            
        except Exception as e:
            logger.error(f"Error guardando certificados para est {estudiante_id}: {e}")
            raise

    @classmethod
    def save_pdf_only(
        cls, 
        evento_id: int, 
        estudiante_id: int, 
        pdf_source_path: str
    ) -> str:
        """
        Almacena solo el archivo PDF (útil para regeneraciones parciales).

        Args:
            evento_id (int): ID del evento.
            estudiante_id (int): ID del estudiante.
            pdf_source_path (str): Ruta temporal del PDF.

        Returns:
            str: Ruta relativa del PDF.
        """
        try:
            dest_dir = cls.get_certificate_directory(evento_id, estudiante_id)
            cls.ensure_directory_exists(dest_dir)
            
            pdf_dest = os.path.join(dest_dir, 'certificado.pdf')
            
            if not os.path.exists(pdf_source_path):
                raise FileNotFoundError(f"Fuente PDF no encontrada: {pdf_source_path}")
            
            shutil.copy2(pdf_source_path, pdf_dest)
            
            media_root = str(settings.MEDIA_ROOT)
            pdf_rel = os.path.relpath(pdf_dest, media_root)
            
            return pdf_rel.replace('\\', '/')
            
        except Exception as e:
            logger.error(f"Error guardando PDF para est {estudiante_id}: {e}")
            raise
    
    @staticmethod
    def get_temp_path(filename: str) -> str:
        """Genera una ruta absoluta segura en el directorio temporal del sistema."""
        return os.path.join(tempfile.gettempdir(), filename)
