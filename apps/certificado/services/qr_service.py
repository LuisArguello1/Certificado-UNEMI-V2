
import os
import io
import logging
import qrcode
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.conf import settings

logger = logging.getLogger(__name__)

class QRService:
    @staticmethod
    def generate_qr_image(data: str) -> io.BytesIO:
        """Genera una imagen QR en memoria."""
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

    @staticmethod
    def stamp_qr_on_pdf(pdf_path: str, uuid_val: str):
        """
        Estampa el código QR de validación en la esquina inferior derecha del PDF.
        Sobrescribe el archivo PDF original.
        """
        try:
            # Obtener URL base
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            validation_url = f"{base_url}/validar/{uuid_val}/"
            
            # Generar QR
            qr_buffer = QRService.generate_qr_image(validation_url)
            
            # Leer PDF original
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            
            # Procesar página(s) - usualmente es solo una
            for i, page in enumerate(reader.pages):
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)
                logger.info(f"Procesando página {i}: {page_width}x{page_height}. Orientación: {'Apaisado' if page_width > page_height else 'Retrato'}")
                
                # Crear PDF temporal con solo el QR (watermark)
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(page_width, page_height))
                
                # Configuración de Posicionamiento (Ajustado)
                qr_size = 60 # Más pequeño como se solicitó
                padding = 40 # Margen equilibrado
                
                # Esquina inferior derecha real (considerando mediabox.left/bottom)
                m_left = float(page.mediabox.left)
                m_bottom = float(page.mediabox.bottom)
                
                x = m_left + page_width - qr_size - padding
                y = m_bottom + padding
                
                # Dibujar QR (Limpio, sin marcos ni texto)
                can.drawImage(ImageReader(qr_buffer), x, y, width=qr_size, height=qr_size)
                
                can.save()

                
                packet.seek(0)
                watermark_reader = PdfReader(packet)
                watermark_page = watermark_reader.pages[0]
                
                # Fusionar (pypdf merge_page pone el contenido al final, es decir, AL FRENTE)
                page.merge_page(watermark_page)
                writer.add_page(page)

            
            # Guardar en archivo temporal para evitar conflictos de lectura/escritura
            temp_output = f"{pdf_path}.tmp"
            with open(temp_output, "wb") as f:
                writer.write(f)
            
            # Reemplazar original
            import shutil
            shutil.move(temp_output, pdf_path)
            
            logger.info(f"QR estampado exitosamente en {pdf_path}. Coordenadas: X={x}, Y={y}")
            return True

            
        except Exception as e:
            logger.error(f"Error al estampar QR en PDF {pdf_path}: {str(e)}", exc_info=True)
            raise e
