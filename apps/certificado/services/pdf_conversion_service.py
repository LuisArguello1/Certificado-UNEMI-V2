"""
Servicio para convertir documentos DOCX a PDF usando LibreOffice.

Este módulo encapsula la lógica de conversión de documentos, manejando
la interacción con el proceso headless de LibreOffice.
"""

import os
import subprocess
import logging
import tempfile
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class PDFConversionError(Exception):
    """Excepción lanzada cuando falla la conversión de DOCX a PDF."""
    pass


class PDFConversionService:
    """
    Servicio para convertir documentos DOCX a PDF usando LibreOffice headless.
    
    Gestiona la ejecución del subproceso, timeouts y perfiles de usuario temporales
    para evitar conflictos de bloqueo.
    """
    
    @staticmethod
    def convert_docx_to_pdf(docx_path: str, output_dir: Optional[str] = None) -> str:
        """
        Convierte un archivo DOCX a PDF.

        Args:
            docx_path (str): Ruta absoluta al archivo .docx.
            output_dir (Optional[str]): Directorio de salida. Si es None, usa el del DOCX.

        Returns:
            str: Ruta absoluta del archivo PDF generado.

        Raises:
            FileNotFoundError: Si el archivo DOCX no existe.
            PDFConversionError: Si ocurre un error en la conversión o timeout.
        """
        try:
            if not os.path.exists(docx_path):
                raise FileNotFoundError(f"Archivo DOCX no encontrado: {docx_path}")
            
            # Configurar directorio de salida
            if output_dir is None:
                output_dir = os.path.dirname(docx_path)
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Configuración de LibreOffice
            libreoffice_path = getattr(settings, 'LIBREOFFICE_PATH', 'soffice')
            
            # Usar perfil compartido para rendimiento y evitar bloqueos en concurrencia
            shared_profile_dir = os.path.join(tempfile.gettempdir(), "LO_shared_profile")
            os.makedirs(shared_profile_dir, exist_ok=True)
            
            # Formato URL para UserInstallation (compatible Windows/Linux)
            user_inst_url = f"file:///{shared_profile_dir.replace(os.sep, '/')}"
            
            # Flags optimizados para ejecución headless segura
            command = [
                libreoffice_path,
                f"-env:UserInstallation={user_inst_url}",
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                '--norestore',          # No intentar restaurar documentos previos
                '--nofirststartwizard', # Saltar wizard de inicio
                '--nologo',             # Sin splash screen
                '--nolockcheck',        # Ignorar archivos de bloqueo .lock
                '--nodefault',          # No iniciar con documento por defecto
                docx_path
            ]
            
            # Configurar startupinfo para ocultar ventana en Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            logger.debug(f"Ejecutando conversión PDF para: {docx_path}")
            
            # Ejecutar conversión con timeout
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,  # Timeout generoso pero seguro
                startupinfo=startupinfo
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Error desconocido"
                logger.error(f"Fallo LibreOffice (Exit Code {result.returncode}): {error_msg}")
                raise PDFConversionError(f"Error convirtiendo PDF: {error_msg}")
            
            # Verificar resultado
            filename = os.path.basename(docx_path)
            pdf_filename = os.path.splitext(filename)[0] + '.pdf'
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            if not os.path.exists(pdf_path):
                # A veces LibreOffice falla silenciosamente o cambia el nombre
                raise PDFConversionError(f"El archivo PDF no se generó en la ruta esperada: {pdf_path}")
                
            return pdf_path
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout (30s) al convertir documento: {docx_path}")
            raise PDFConversionError("La conversión excedió el tiempo límite.")
            
        except Exception as e:
            if isinstance(e, (FileNotFoundError, PDFConversionError)):
                raise
            logger.error(f"Excepción no manejada en conversión PDF: {e}", exc_info=True)
            raise PDFConversionError(f"Error interno de conversión: {e}")

    @staticmethod
    def convert_batch_docx_to_pdf(docx_paths: list[str], output_dir: Optional[str] = None) -> dict[str, str]:
        """
        Convierte múltiples archivos DOCX a PDF en UNA SOLA ejecución de LibreOffice.
        
        Esta optimización reduce drásticamente el tiempo total al amortizar
        el costo de inicio del proceso soffice.

        Args:
            docx_paths: Lista de rutas absolutas a archivos .docx
            output_dir: Directorio de salida. Si es None, usa el directorio del primer archivo.

        Returns:
            Dict[docx_path, pdf_path]: Mapeo de archivos convertidos exitosamente.
        """
        if not docx_paths:
            return {}

        try:
            # Validación básica
            valid_paths = [p for p in docx_paths if os.path.exists(p)]
            if not valid_paths:
                logger.warning("Ningún archivo DOCX válido para conversión por lotes.")
                return {}

            # Definir directorio de salida común
            if output_dir is None:
                output_dir = os.path.dirname(valid_paths[0])
            os.makedirs(output_dir, exist_ok=True)

            # Configuración LibreOffice (reutilizando lógica)
            libreoffice_path = getattr(settings, 'LIBREOFFICE_PATH', 'soffice')
            shared_profile_dir = os.path.join(tempfile.gettempdir(), "LO_shared_profile")
            os.makedirs(shared_profile_dir, exist_ok=True)
            user_inst_url = f"file:///{shared_profile_dir.replace(os.sep, '/')}"

            # Construir comando con TODOS los archivos
            # soffice --headless --convert-to pdf --outdir <dir> file1.docx file2.docx ...
            command = [
                libreoffice_path,
                f"-env:UserInstallation={user_inst_url}",
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                '--norestore',
                '--nofirststartwizard',
                '--nologo',
                '--nolockcheck',
                '--nodefault'
            ] + valid_paths  # Adjuntar todos los archivos al comando

            # Configuración Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            logger.info(f"Iniciando conversión batch de {len(valid_paths)} archivos...")
            
            # Timeout dinámico: 15s base + 3s por archivo adicional
            timeout = 15 + (3 * len(valid_paths))

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                startupinfo=startupinfo
            )

            if result.returncode != 0:
                logger.error(f"Error parcial/total en batch LibreOffice: {result.stderr or result.stdout}")
                # No lanzamos excepción aquí para intentar recuperar los que sí se generaron
            
            # Verificar resultados y construir mapa de retorno
            conversion_map = {}
            for docx_path in valid_paths:
                filename = os.path.basename(docx_path)
                pdf_filename = os.path.splitext(filename)[0] + '.pdf'
                pdf_path = os.path.join(output_dir, pdf_filename)
                
                if os.path.exists(pdf_path):
                    conversion_map[docx_path] = pdf_path
                else:
                    logger.warning(f"Fallo conversión individual en batch: {docx_path}")

            logger.info(f"Conversión batch finalizada. Exitosos: {len(conversion_map)}/{len(valid_paths)}")
            return conversion_map

        except Exception as e:
            logger.error(f"Error crítico en conversión batch: {e}", exc_info=True)
            raise PDFConversionError(f"Fallo en batch processing: {e}")
    
    @staticmethod
    def verify_libreoffice_installed() -> bool:
        """
        Verifica la disponibilidad del binario de LibreOffice.

        Returns:
            bool: True si se puede ejecutar, False en caso contrario.
        """
        try:
            libreoffice_path = getattr(settings, 'LIBREOFFICE_PATH', 'soffice')
            
            # Sin flags complejos, solo versión
            result = subprocess.run(
                [libreoffice_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            is_valid = result.returncode == 0
            if is_valid:
                logger.debug(f"LibreOffice detectado: {result.stdout.strip()}")
            else:
                logger.warning(f"LibreOffice retornó error al verificar versión: {result.stderr}")
                
            return is_valid
            
        except FileNotFoundError:
            logger.warning("Ejecutable de LibreOffice no encontrado en el PATH o ruta configurada.")
            return False
        except Exception as e:
            logger.warning(f"Error verificando LibreOffice: {e}")
            return False
