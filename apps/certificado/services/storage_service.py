"""
Servicio de almacenamiento para archivos de certificados.

Gestiona la organización física de archivos DOCX y PDF usando Django's default_storage,
que puede ser local o Azure Blob Storage según la configuración.
"""

import os
import logging
import tempfile
from typing import Tuple
from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class CertificateStorageService:
    """
    Servicio para persistencia y organización de archivos generados.
    
    Patrón de almacenamiento:
        certificados/{evento_id}/{nombres_estudiante}.{ext}
    
    Compatible con almacenamiento local y Azure Blob Storage.
    """
    
    @staticmethod
    def get_certificate_path(evento_id: int, estudiante_id: int, filename: str, nombres_estudiante: str = None) -> str:
        """
        Calcula la ruta relativa para almacenar un archivo de certificado.

        Args:
            evento_id (int): ID del evento.
            estudiante_id (int): ID del estudiante (usado como fallback si no hay nombres).
            filename (str): Nombre del archivo base (ej: 'certificado.pdf')
            nombres_estudiante (str): Nombres completos del estudiante (opcional)

        Returns:
            str: Ruta relativa al almacenamiento (ej: 'certificados/1/Juan_Perez.pdf')
        """
        # Usar nombres del estudiante si está disponible, sino usar ID
        if nombres_estudiante:
            # Limpiar el nombre: reemplazar espacios y caracteres especiales
            import re
            nombre_limpio = re.sub(r'[^\w\s-]', '', nombres_estudiante)  # Eliminar caracteres especiales
            nombre_limpio = re.sub(r'\s+', '_', nombre_limpio.strip())  # Espacios -> guiones bajos
            
            # Obtener la extensión del filename
            ext = filename.split('.')[-1] if '.' in filename else 'pdf'
            archivo_nombre = f'{nombre_limpio}.{ext}'
        else:
            archivo_nombre = filename
        
        return f'certificados/{evento_id}/{archivo_nombre}'
    
    @classmethod
    def save_certificate_files(
        cls, 
        evento_id: int, 
        estudiante_id: int,
        docx_source_path: str, 
        pdf_source_path: str,
        nombres_estudiante: str = None
    ) -> Tuple[str, str]:
        """
        Almacena el par de archivos (DOCX, PDF) en el storage configurado.

        Lee los archivos desde su ubicación temporal y los sube al storage
        (local o Azure según configuración).

        Args:
            evento_id (int): ID del evento.
            estudiante_id (int): ID del estudiante.
            docx_source_path (str): Ruta absoluta del DOCX temporal.
            pdf_source_path (str): Ruta absoluta del PDF temporal.
            nombres_estudiante (str): Nombres completos del estudiante (opcional).

        Returns:
            Tuple[str, str]: (docx_relative_path, pdf_relative_path) relativas al storage.

        Raises:
            FileNotFoundError: Si los archivos fuente no existen.
            Exception: Si hay error al subir los archivos.
        """
        try:
            # Validar que existen los archivos fuente
            if not os.path.exists(docx_source_path):
                raise FileNotFoundError(f"Fuente DOCX no encontrada: {docx_source_path}")
            
            if not os.path.exists(pdf_source_path):
                raise FileNotFoundError(f"Fuente PDF no encontrada: {pdf_source_path}")
            
            # Definir rutas relativas en el storage
            docx_path = cls.get_certificate_path(evento_id, estudiante_id, 'certificado.docx', nombres_estudiante)
            pdf_path = cls.get_certificate_path(evento_id, estudiante_id, 'certificado.pdf', nombres_estudiante)
            
            # Leer y guardar DOCX
            with open(docx_source_path, 'rb') as docx_file:
                # Si ya existe, lo eliminamos primero
                if default_storage.exists(docx_path):
                    default_storage.delete(docx_path)
                # Guardamos el nuevo archivo
                default_storage.save(docx_path, File(docx_file))
            
            # Leer y guardar PDF
            with open(pdf_source_path, 'rb') as pdf_file:
                if default_storage.exists(pdf_path):
                    default_storage.delete(pdf_path)
                default_storage.save(pdf_path, File(pdf_file))
            
            logger.info(f"Archivos guardados en storage para estudiante {estudiante_id}")
            
            # Retornar rutas relativas (Django las usa para FileField)
            return (docx_path, pdf_path)
            
        except Exception as e:
            logger.error(f"Error guardando certificados para est {estudiante_id}: {e}")
            raise

    @classmethod
    def save_pdf_only(
        cls, 
        evento_id: int, 
        estudiante_id: int, 
        pdf_source_path: str,
        nombres_estudiante: str = None
    ) -> str:
        """
        Almacena solo el archivo PDF (útil para regeneraciones parciales).

        Args:
            evento_id (int): ID del evento.
            estudiante_id (int): ID del estudiante.
            pdf_source_path (str): Ruta temporal del PDF.
            nombres_estudiante (str): Nombres completos del estudiante (opcional).

        Returns:
            str: Ruta relativa del PDF en el storage.
        """
        try:
            if not os.path.exists(pdf_source_path):
                raise FileNotFoundError(f"Fuente PDF no encontrada: {pdf_source_path}")
            
            pdf_path = cls.get_certificate_path(evento_id, estudiante_id, 'certificado.pdf', nombres_estudiante)
            
            with open(pdf_source_path, 'rb') as pdf_file:
                if default_storage.exists(pdf_path):
                    default_storage.delete(pdf_path)
                default_storage.save(pdf_path, File(pdf_file))

            return pdf_path
            
        except Exception as e:
            logger.error(f"Error guardando PDF para est {estudiante_id}: {e}")
            raise
    
    @staticmethod
    def get_temp_path(filename: str) -> str:
        """Genera una ruta absoluta segura en el directorio temporal del sistema."""
        return os.path.join(tempfile.gettempdir(), filename)
