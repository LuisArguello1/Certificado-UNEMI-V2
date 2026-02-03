"""
Servicio para la generación e incrustación de códigos QR en documentos PDF.

Permite generar códigos QR de validación y estamparlos en la primera página
de los certificados generados.
"""

import os
import io
import shutil
import logging
import qrcode
from typing import IO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.conf import settings

logger = logging.getLogger(__name__)


class QRService:
    """
    Servicio de gestión de códigos QR.
    
    Responsabilidades:
    - Generar imagen QR a partir de URL de validación.
    - Estampar imagen QR en documentos PDF existentes.
    """

    @staticmethod
    def generate_qr_image(data: str) -> io.BytesIO:
        """
        Genera una imagen QR en memoria formato PNG.

        Args:
            data (str): Texto o URL a codificar.

        Returns:
            io.BytesIO: Buffer conteniendo la imagen PNG.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    @classmethod
    def stamp_qr_on_pdf(cls, pdf_path: str, uuid_val: str) -> bool:
        """
        Estampa el código QR de validación en la esquina inferior derecha 
        SOLAMENTE de la PRIMERA PÁGINA del PDF.

        Args:
            pdf_path (str): Ruta absoluta al archivo PDF.
            uuid_val (str): UUID único del certificado para construir la URL.

        Returns:
            bool: True si el proceso fue exitoso.

        Raises:
            IOError: Si hay problemas leyendo/escribiendo el archivo.
        """
        temp_output = f"{pdf_path}.tmp"
        
        try:
            # 1. Construir URL de validación
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
            validation_url = f"{base_url}/validar/{uuid_val}/"
            
            # 2. Generar imagen QR
            qr_buffer = cls.generate_qr_image(validation_url)
            
            # 3. Leer PDF original
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            
            # 4. Procesar páginas
            for i, page in enumerate(reader.pages):
                # SOLO estampar en la primera página (índice 0)
                if i == 0:
                    cls._stamp_page(page, qr_buffer)
                
                # Añadir página (estampada o no) al writer
                writer.add_page(page)
            
            # 5. Guardar en archivo temporal
            with open(temp_output, "wb") as f:
                writer.write(f)
            
            # 6. Reemplazo atómico
            shutil.move(temp_output, pdf_path)
            
            logger.debug(f"QR estampado exitosamente en pagina 1 de: {pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error estampando QR en {pdf_path}: {e}", exc_info=True)
            # Limpieza en caso de error
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except OSError:
                    pass
            raise

    @staticmethod
    def _stamp_page(page, qr_buffer: io.BytesIO) -> None:
        """
        Método auxiliar para aplicar el watermark a una página específica.
        Calcula posición dinámica basándose en el tamaño de la página.
        """
        try:
            # Dimensiones
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # Configuración
            qr_size = 60
            padding = 40
            
            # Coordenadas: Esquina inferior derecha
            m_left = float(page.mediabox.left)
            m_bottom = float(page.mediabox.bottom)
            
            x = m_left + page_width - qr_size - padding
            y = m_bottom + padding
            
            # Crear PDF canvas en memoria (watermark)
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            can.drawImage(ImageReader(qr_buffer), x, y, width=qr_size, height=qr_size)
            can.save()
            packet.seek(0)
            
            # Merge
            watermark_reader = PdfReader(packet)
            if watermark_reader.pages:
                page.merge_page(watermark_reader.pages[0])
                
        except Exception as e:
            logger.warning(f"Error calculado posición QR: {e}")
            # No relanzamos para no romper todo el proceso si falla el cálculo,
            # aunque idealmente debería funcionar siempre.
            raise e
