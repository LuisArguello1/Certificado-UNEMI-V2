import os
import json
import uuid
import qrcode
import io
import re
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

class CertificateService:
    """
    Servicio para generar certificados en PDF de alta fidelidad.
    Maneja arquitectura multi-bloque dinámica con reemplazo de variables garantizado.
    """
    
    @staticmethod
    def format_date_es(date):
        if not date: return "N/A"
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio", 
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        return f"{date.day} de {meses[date.month-1]} de {date.year}"

    @staticmethod
    def generate_pdf(certificado):
        estudiante = certificado.estudiante
        curso = estudiante.curso
        plantilla = certificado.plantilla or curso.plantilla_certificado
        config = curso.configuracion_certificado 
        
        if not plantilla or not config: return None

        # Asegurar código de verificación
        if not certificado.codigo_verificacion:
            certificado.codigo_verificacion = str(uuid.uuid4())[:13].upper().replace('-', '')
            certificado.save(update_fields=['codigo_verificacion'])

        # Mapeo de valores dinámicos CORE para reemplazo forzado
        # Esto asegura que incluso si el usuario editó el texto en el diseñador,
        # los valores del alumno actual se inyecten correctamente.
        replacements = {
            'NOMBRE DEL ESTUDIANTE': estudiante.nombre_completo.strip().upper(),
            'NOMBRE DEL CURSO': curso.nombre.strip().upper(),
            'CEDULA': estudiante.cedula,
            'RESPONSABLE': curso.responsable.strip(),
            'FECHA_INICIO': CertificateService.format_date_es(curso.fecha_inicio),
            'FECHA_FIN': CertificateService.format_date_es(curso.fecha_fin),
            'FECHA_EMISION': CertificateService.format_date_es(certificado.fecha_generacion),
        }

        # Valores por defecto para bloques si no tienen placeholder
        # Esto previene el error donde el diseñador guarda "ARELIS RUIZ" como texto estático
        block_type_defaults = {
            'student': '[NOMBRE DEL ESTUDIANTE]',
            'course': '"[NOMBRE DEL CURSO]"',
            'responsible': 'bajo la responsabilidad de [RESPONSABLE].',
            'dates': 'con una duración desde [FECHA_INICIO] hasta [FECHA_FIN],',
            'footer': 'En constancia se expide el presente el [FECHA_EMISION].'
        }

        buffer = io.BytesIO()
        bg_img = ImageReader(plantilla.archivo.path)
        img_w, img_h = bg_img.getSize()

        p = canvas.Canvas(buffer, pagesize=(img_w, img_h))
        p.drawImage(bg_img, 0, 0, width=img_w, height=img_h)

        # RENDERIZAR CADA BLOQUE CONFIGURADO
        for block_id, block_conf in config.items():
            if not isinstance(block_conf, dict): continue
            
            block_type = block_conf.get('type', '')
            raw_text = block_conf.get('text_override', "")
            
            # PROTECCIÓN: Si es un bloque de tipo 'student' y no tiene el placeholder ni el nombre real del alumno,
            # pero tiene el nombre de ejemplo que se guardó en el diseñador, lo forzamos al placeholder.
            # O simplemente aplicamos el default del tipo si el texto parece "sucio".
            if not raw_text or (block_type in block_type_defaults and 'ARELIS RUIZ' in raw_text.upper()):
                raw_text = block_type_defaults.get(block_type, raw_text)

            # Procesar REEMPLAZOS (soporta {VAR} y [VAR])
            processed_text = raw_text
            for key, val in replacements.items():
                processed_text = processed_text.replace(f'{{{key}}}', str(val))
                processed_text = processed_text.replace(f'[{key}]', str(val))
            
            try:
                # --- CALCULO DE ESCALA ---
                container_w = float(block_conf.get('container_w', 1000))
                scale_factor = img_w / container_w if container_w > 0 else 1.0
                
                font_size = float(block_conf.get('font_size', 20)) * scale_factor
                color_hex = block_conf.get('color', '#000000')
                
                # Coordenadas (Pivot Central)
                x_pct = float(block_conf.get('x', 50))
                y_pct = float(block_conf.get('y', 40))
                
                x_pos = (x_pct / 100) * img_w
                y_pos = img_h - ((y_pct / 100) * img_h)

                # Fuente
                font_variant = "Helvetica"
                if block_conf.get('bold'): font_variant = "Helvetica-Bold"
                if block_conf.get('italic'): 
                    font_variant = "Helvetica-Oblique" if font_variant == "Helvetica" else "Helvetica-BoldOblique"
                
                p.setFont(font_variant, font_size)
                p.setFillColor(HexColor(color_hex))
                
                p.drawCentredString(x_pos, y_pos, processed_text)

            except Exception as e:
                print(f"Error renderizando bloque {block_id}: {e}")

        # QR
        try:
            ver_url = f"https://certificados.unemi.edu.ec/verificar/{certificado.codigo_verificacion}/"
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(ver_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buf = io.BytesIO()
            qr_img.save(qr_buf, format='PNG')
            qr_buf.seek(0)
            
            qr_size = img_w * 0.08 
            p.drawImage(ImageReader(qr_buf), img_w - qr_size - (img_w*0.05), (img_h*0.05), width=qr_size, height=qr_size)
        except Exception as e:
            print(f"Error QR: {e}")

        p.showPage()
        p.save()

        filename = f"certificado_{estudiante.cedula}_{curso.id}.pdf"
        buffer.seek(0)
        certificado.archivo_generado.save(filename, ContentFile(buffer.read()), save=True)
        return certificado
