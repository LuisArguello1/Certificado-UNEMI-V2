import os
import json
import uuid
import qrcode
import io
import base64
from pathlib import Path
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

# Try importing WeasyPrint, handle if missing to prevent immediate crash during dev
try:
    from weasyprint import HTML, CSS
except ImportError:
    HTML = None

class CertificateService:
    """
    Motor de renderizado de certificados usando WeasyPrint.
    Convierte el JSON del editor visual a un layout HTML/CSS idéntico
    y genera el PDF final preservando fidelidad visual.
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
    def format_name(full_name, mode='full'):
        """
        Formatea el nombre del estudiante según el modo solicitado:
        - full: Juan Carlos Perez Lopez (Defecto)
        - first_last: Juan Perez
        - f_last: J. Perez
        - first_l: Juan P.
        - fl: J. P.
        """
        if not full_name: return ""
        parts = full_name.split()
        if not parts: return ""
        
        if mode == 'full':
            return full_name
        
        first = parts[0]
        last = parts[-1] if len(parts) > 1 else ""
        
        if mode == 'first_last':
            return f"{first} {last}".strip()
        elif mode == 'f_last':
            return f"{first[0]}. {last}".strip()
        elif mode == 'first_l':
            return f"{first} {last[0]}.".strip() if last else first
        elif mode == 'fl':
            return f"{first[0]}. {last[0]}.".strip() if last else f"{first[0]}."
            
        return full_name

    @staticmethod
    def generate_pdf(certificado):
        # Verificación de librería
        if not HTML:
            print("CRITICAL: WeasyPrint no está instalado.")
            return None

        estudiante = certificado.estudiante
        curso = estudiante.curso
        plantilla = certificado.plantilla or curso.plantilla_certificado
        config = curso.configuracion_certificado 
        
        if not plantilla or not config: 
            return None

        if not certificado.codigo_verificacion:
            certificado.codigo_verificacion = str(uuid.uuid4())[:13].upper().replace('-', '')
            certificado.save(update_fields=['codigo_verificacion'])

        # --- DATA INJECTION LAYER ---
        # Note: We delay name injection to handle formatting per-block if needed
        replacements = {
            'NOMBRE DEL CURSO': curso.nombre.strip().upper(),
            'CEDULA': estudiante.cedula,
            'RESPONSABLE': curso.responsable.strip(),
            'FECHA_INICIO': CertificateService.format_date_es(curso.fecha_inicio),
            'FECHA_FIN': CertificateService.format_date_es(curso.fecha_fin),
            'FECHA_EMISION': CertificateService.format_date_es(certificado.fecha_generacion),
        }

        # --- BACKGROUND & DIMENSIONS ---
        bg_uri = ""
        img_w = 800
        img_h = 600
        
        try:
            from apps.core.services.storage_service import StorageService
            # Obtener path absoluto de forma segura desde el NAS
            bg_path_abs_str = StorageService.safe_get_path(plantilla.archivo)
            
            if not bg_path_abs_str:
                print(f"Error: Plantilla no encontrada físicamente en el NAS: {plantilla.archivo.name}")
                return None
                
            bg_path_abs = Path(bg_path_abs_str).resolve()
            bg_uri = bg_path_abs.as_uri()
            
            with Image.open(bg_path_abs) as img:
                img_w, img_h = img.size
        except Exception as e:
            print(f"Error cargando imagen de fondo: {e}")
            return None

        # --- BLOCK PROCESSING ---
        render_blocks = []
        
        for block_id, block in config.items():
            if not isinstance(block, dict): continue
            
            # 1. Recuperar contenido y resolver variables
            raw_text = block.get('text_override', block.get('text', ''))
            content = raw_text
            
            # Special handling for student name with formatting
            if 'NOMBRE DEL ESTUDIANTE' in replacements or '[NOMBRE DEL ESTUDIANTE]' in content:
                # Determine format mode for this specific block
                fmt_mode = block.get('name_format', 'full')
                formatted_name = CertificateService.format_name(estudiante.nombre_completo.strip().upper(), fmt_mode)
                
                content = content.replace('{NOMBRE DEL ESTUDIANTE}', formatted_name)
                content = content.replace('[NOMBRE DEL ESTUDIANTE]', formatted_name)

            for key, val in replacements.items():
                content = content.replace(f'{{{key}}}', str(val))
                content = content.replace(f'[{key}]', str(val))
            
            content = content.strip()
            if not content: continue

            # 2. Layout Engine: Normalización de Coordenadas
            try:
                if 'x_px' in block and 'y_px' in block:
                    x_px = float(block.get('x_px', 0))
                    y_px = float(block.get('y_px', 0))
                    width_px = float(block.get('width_px', 300))
                    font_size = float(block.get('font_size', 24))
                else:
                    # Legacy fallback
                    x_pct = float(block.get('x', block.get('x_pct', 50)))
                    y_pct = float(block.get('y', block.get('y_pct', 50)))
                    width_pct = float(block.get('width_pct', 30))
                    container_w = float(block.get('container_w', img_w) or img_w)
                    scale = img_w / container_w
                    x_px = (x_pct / 100) * img_w
                    y_px = (y_pct / 100) * img_h
                    width_px = (width_pct / 100) * img_w
                    font_size = float(block.get('font_size', 24)) * scale

                # CORRECCIÓN DE POSICIONAMIENTO PARA TEXTO (Reset para calibración estructural)
                if block.get('type') != 'image':
                    # Compensamos el "leading" o espacio superior de la fuente
                    # WeasyPrint suele añadir un ~25% de espacio arriba del baseline.
                    drift_factor = 0.25 
                    y_px -= (font_size * drift_factor)

                # 3. Style Engine - Font Mapping para WeasyPrint
                raw_font = block.get('font_family', 'Arial')
                
                # Limpiar comillas y sufijos
                font_family_clean = raw_font.replace("'", "").replace('"', "")
                for suffix in [', sans-serif', ', serif', ', monospace', ', cursive', ', fantasy']:
                    font_family_clean = font_family_clean.replace(suffix, "").strip()
                
                # SOLUCIÓN: Usar familias genéricas de CSS que WeasyPrint SIEMPRE puede renderizar
                # En lugar de intentar mapear fuentes específicas que pueden o no estar instaladas,
                # usamos los fallbacks genéricos de CSS que están garantizados en todos los sistemas
                font_generic_mapping = {
                    'Arial': 'sans-serif',
                    'Verdana': 'sans-serif',
                    'Times New Roman': 'serif',
                    'Georgia': 'serif',
                    'Courier New': 'monospace',
                    'Ubuntu': 'sans-serif',
                    'Noto Sans': 'sans-serif',
                    'Noto Serif': 'serif',
                    'Liberation Sans': 'sans-serif',
                    'Liberation Serif': 'serif',
                }
                
                # Obtener la familia genérica
                generic = font_generic_mapping.get(font_family_clean, 'sans-serif')
                
                # Formato final: "DejaVu Sans, sans-serif" o solo "serif"
                # Intentamos usar la fuente Linux específica como primera opción, con fallback genérico
                linux_fonts = {
                    'Arial': 'DejaVu Sans',
                    'Verdana': 'DejaVu Sans',
                    'Times New Roman': 'DejaVu Serif',
                    'Georgia': 'DejaVu Serif',
                    'Courier New': 'DejaVu Sans Mono',
                    'Ubuntu': 'Ubuntu',
                    'Noto Sans': 'Noto Sans',
                    'Noto Serif': 'Noto Serif',
                    'Liberation Sans': 'Liberation Sans',
                    'Liberation Serif': 'Liberation Serif',
                }
                
                linux_font = linux_fonts.get(font_family_clean, None)
                if linux_font:
                    final_font = f"{linux_font}, {generic}"
                else:
                    final_font = generic
                
                # IMPORTANTE: Formatear floats a strings con punto decimal para CSS
                # Django L10N puede convertir 10.5 a "10,5" lo cual rompe CSS
                src = block.get('src', '')
                # Fix for WeasyPrint: Convert /media/ path to file:// absolute path
                if block.get('type') == 'image' and src.startswith(settings.MEDIA_URL):
                    # Remove MEDIA_URL prefix to get relative path
                    rel_path = src.replace(settings.MEDIA_URL, '', 1)
                    # Join with MEDIA_ROOT
                    abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
                    # Convert to file URI
                    src = Path(abs_path).as_uri()

                render_blocks.append({
                    'id': block_id,
                    'text': content,
                    'x': f"{x_px:.2f}",
                    'y': f"{y_px:.2f}",
                    'width': f"{width_px:.2f}",
                    'height': f"{float(block.get('height_px')):.2f}" if block.get('height_px') else None,
                    'fontSize': f"{font_size:.2f}",
                    'color': block.get('color', '#000000'),
                    'textAlign': block.get('text_align') or block.get('textAlign', 'center'),
                    'fontFamily': final_font,
                    'bold': block.get('bold', False),
                    'italic': block.get('italic', False),
                    'underline': block.get('underline', False),
                    'letterSpacing': f"{float(block.get('letter_spacing', block.get('letterSpacing', 0))):.2f}",
                    'opacity': f"{float(block.get('opacity', 1)):.2f}",
                    'rotation': block.get('rotation', 0),
                    'type': block.get('type', 'textbox'),
                    'src': src
                })
                
                # DEBUG: Log font mapping
                print(f"[FONT DEBUG] Block {block_id}: {raw_font} -> {font_family_clean} -> {final_font}")

            except Exception as e:
                print(f"Error procesando bloque {block_id}: {e}")

        # --- QR CODE GENERATION (DISABLED) ---
        qr_data = None
        # try:
        #     ver_url = f"https://certificados.unemi.edu.ec/verificar/{certificado.codigo_verificacion}/"
        #     qr = qrcode.QRCode(version=1, box_size=1, border=0)
        #     qr.add_data(ver_url)
        #     qr.make(fit=True)
        #     qr_img = qr.make_image(fill_color="black", back_color="white")
        #     
        #     qr_buffer = io.BytesIO()
        #     qr_img.save(qr_buffer, format='PNG')
        #     qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')
        #     
        #     # Tamaño QR: 8% del ancho
        #     qr_target_size = img_w * 0.08
        #     qr_margin = img_w * 0.05
        #     
        #     qr_x = img_w - qr_target_size - qr_margin
        #     qr_y = img_h - qr_target_size - (img_h * 0.05)
        #     
        #     qr_data = {
        #         'image': qr_base64,
        #         'x': f"{qr_x:.2f}",
        #         'y': f"{qr_y:.2f}",
        #         'width': f"{qr_target_size:.2f}"
        #     }
        #
        # except Exception as e:
        #     print(f"Error generando QR: {e}")

        # --- HTML RENDER ---
        context = {
            'width': img_w,
            'height': img_h,
            'bg_uri': bg_uri, # Usamos bg_uri en lugar de path raw
            'blocks': render_blocks,
            'qr_data': qr_data
        }
        
        html_string = render_to_string('curso/certificate/pdf_render.html', context)

        # --- PDF GENERATION ---
        buffer = io.BytesIO()
        # base_url debe ser un path de directorio
        HTML(string=html_string, base_url=str(Path(settings.MEDIA_ROOT))).write_pdf(target=buffer)
        
        # --- SAVING ---
        try:
            filename = f"certificado_{estudiante.cedula}_{curso.id}.pdf"
            buffer.seek(0)
            
            # Verificar si el directorio existe (aunque Django lo maneja, esto es por robustez extra en NAS)
            storage_online, _ = StorageService.check_storage_health()
            if not storage_online:
                print("Error: NAS fuera de línea durante guardado de PDF")
                return None

            certificado.archivo_generado.save(filename, ContentFile(buffer.read()), save=True)
            return certificado
        except Exception as e:
            print(f"Error crítico guardando PDF en NAS: {e}")
            return None
