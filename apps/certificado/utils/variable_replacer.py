
import re
import logging
from typing import Dict, List
from docx import Document
from docx.shared import Pt, Inches, Twips
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


logger = logging.getLogger(__name__)


class VariableReplacer:
    """
    Reemplazador de variables que preserva el formato EXACTO de la plantilla.
    """
    
    @staticmethod
    def replace_in_document(doc_path: str, variables: Dict[str, str]) -> Document:
        """
        Carga un documento Word y reemplaza todas las variables PRESERVANDO TODO EL FORMATO.
        """
        try:
            doc = Document(doc_path)
            
            # Normalizar variables (espacios y guiones bajos)
            variables_normalized = {}
            for k, v in variables.items():
                key_upper = k.upper()
                variables_normalized[key_upper] = v
                
                if ' ' in key_upper:
                    variables_normalized[key_upper.replace(' ', '_')] = v
                elif '_' in key_upper:
                    variables_normalized[key_upper.replace('_', ' ')] = v
            
            # Reemplazar en párrafos del documento principal
            VariableReplacer._replace_in_paragraphs(doc.paragraphs, variables_normalized)
            
            # Reemplazar en tablas
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        VariableReplacer._replace_in_paragraphs(cell.paragraphs, variables_normalized)
            
            # Reemplazar en headers y footers
            for section in doc.sections:
                VariableReplacer._replace_in_paragraphs(section.header.paragraphs, variables_normalized)
                VariableReplacer._replace_in_paragraphs(section.footer.paragraphs, variables_normalized)
            
            # Aplicar ajustes post-procesamiento
            VariableReplacer._apply_post_processing(doc, variables_normalized)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error al reemplazar variables: {str(e)}")
            raise
    
    @staticmethod
    def _apply_post_processing(doc: Document, variables: Dict[str, str]):
        """
        Aplica ajustes de formato después del reemplazo de variables.
        
        - Interlineado 0.5 para el objetivo del programa
        - Sangrías laterales para el párrafo de "Por su..."
        - Espacio adicional antes del contenido para que no suba
        """
        objetivo_value = variables.get('OBJETIVO DEL PROGRAMA', '') or variables.get('OBJETIVO_PROGRAMA', '')
        tipo_value = variables.get('TIPO', '')
        nombres_value = variables.get('NOMBRES', '')
        
        def process_paragraphs(paragraphs):
            for i, paragraph in enumerate(paragraphs):
                text = paragraph.text.strip()
                
                # 1. Párrafos del bloque principal del certificado - agregar sangrías laterales
                # SOLUCIÓN INTELIGENTE: Detectar el inicio del bloque y aplicar sangrías
                # a todos los párrafos consecutivos hasta encontrar un párrafo vacío o la firma
                
                # Detectar si este párrafo es parte del bloque del certificado
                es_inicio_bloque = text.startswith('Por su')
                
                # Detectar contenido que indica que es parte del bloque
                es_contenido_bloque = (
                    # Palabras clave del bloque
                    'La Universidad Estatal' in text or
                    'expide el presente' in text or
                    'Gestión de Educación' in text or
                    'Escuela de Formación' in text or
                    # Contiene fechas típicas del certificado
                    'días del mes de' in text or
                    'del mes de' in text or
                    # Contiene duración
                    'hora(s)' in text or
                    'horas,' in text or
                    # Párrafos cortos que son continuación (como "20 días del mes...")
                    (len(text) > 5 and len(text) < 60 and ('del' in text.lower() or 'de' in text.lower()) and i > 0)
                )
                
                # También verificar si el párrafo anterior tenía sangrías (continuación del bloque)
                tiene_sangria_anterior = False
                if i > 0 and len(paragraphs) > i:
                    try:
                        prev_paragraph = paragraphs[i - 1]
                        prev_left = prev_paragraph.paragraph_format.left_indent
                        if prev_left and prev_left >= Inches(0.5):
                            # El anterior tenía sangría, este podría ser continuación
                            # Solo si este párrafo no está vacío y no parece una firma
                            if text and not text.startswith('Ph.') and 'Vicerrector' not in text:
                                tiene_sangria_anterior = True
                    except:
                        pass
                
                es_bloque_certificado = es_inicio_bloque or es_contenido_bloque or tiene_sangria_anterior
                
                if es_bloque_certificado:
                    try:
                        # Sangría izquierda y derecha
                        paragraph.paragraph_format.left_indent = Inches(1.2)
                        paragraph.paragraph_format.right_indent = Inches(1.2)
                    except Exception as e:
                        logger.warning(f"No se pudo aplicar sangría: {e}")
                
                # 2. Párrafo del objetivo del programa - interlineado reducido
                if objetivo_value and objetivo_value[:50] in text:
                    try:
                        # Interlineado simple reducido
                        paragraph.paragraph_format.line_spacing = Pt(8)
                        paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                        paragraph.paragraph_format.space_after = Pt(0)
                    except Exception as e:
                        logger.warning(f"No se pudo aplicar interlineado: {e}")
                
                # 3. Párrafo con el nombre del estudiante - agregar espacio antes y tamaño de letra
                if nombres_value and nombres_value in text and len(text) < 100:
                    try:
                        # Agregar mucho más espacio antes del nombre para que baje
                        paragraph.paragraph_format.space_before = Pt(24)
                        
                        # Aumentar tamaño de letra a 22pt
                        for run in paragraph.runs:
                            run.font.size = Pt(22)
                    except Exception as e:
                        logger.warning(f"No se pudo aplicar espacio antes: {e}")
        
        # Procesar párrafos principales
        process_paragraphs(doc.paragraphs)
        
        # Procesar tablas
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    process_paragraphs(cell.paragraphs)

    @staticmethod
    def _replace_in_paragraphs(paragraphs, variables: Dict[str, str]):
        """Reemplaza variables en una lista de párrafos."""
        for paragraph in paragraphs:
            VariableReplacer._replace_in_paragraph(paragraph, variables)
    
    @staticmethod
    def _replace_in_paragraph(paragraph, variables: Dict[str, str]):
        """
        Reemplaza variables SIN destruir la estructura del párrafo.
        PRESERVA la fuente y formato original de cada run.
        """
        # 1. Obtener texto completo del párrafo
        runs = paragraph.runs
        if not runs:
            return
        
        full_text = ''.join([run.text for run in runs])
        
        if '{{' not in full_text:
            return
        
        # 2. Encontrar todas las variables en el texto
        pattern = r'\{\{[A-ZÁÉÍÓÚÑa-záéíóúñ_ ]+\}\}'
        matches = list(re.finditer(pattern, full_text))
        
        if not matches:
            return
        
        # 3. Para cada variable, reemplazar en los runs apropiados
        # Trabajamos de atrás hacia adelante para no afectar índices
        for match in reversed(matches):
            var_placeholder = match.group()
            var_name = var_placeholder[2:-2].strip().upper()
            
            # Buscar valor en variables
            value = None
            if var_name in variables:
                value = str(variables[var_name])
            elif var_name.replace(' ', '_') in variables:
                value = str(variables[var_name.replace(' ', '_')])
            elif var_name.replace('_', ' ') in variables:
                value = str(variables[var_name.replace('_', ' ')])
            
            if value is None:
                continue  # Variable no encontrada, dejar como está
            
            # Aplicar transformación si es nombre (pero no curso ni evento)
            if 'NOMBRE' in var_name and 'CURSO' not in var_name and 'EVENTO' not in var_name:
                value = value.upper()
            
            # 4. Reemplazar en los runs correspondientes preservando formato
            VariableReplacer._replace_text_in_runs(
                runs, 
                match.start(), 
                match.end(), 
                value
            )
    
    @staticmethod
    def _replace_text_in_runs(runs, start_pos: int, end_pos: int, replacement: str):
        """
        Reemplaza texto desde start_pos hasta end_pos en los runs,
        preservando el formato del primer run afectado.
        """
        current_pos = 0
        first_run_found = False
        
        for i, run in enumerate(runs):
            run_start = current_pos
            run_end = current_pos + len(run.text)
            
            # Caso 1: Este run contiene el INICIO de la variable
            if not first_run_found and run_start <= start_pos < run_end:
                first_run_found = True
                
                # Texto antes de la variable
                prefix = run.text[:start_pos - run_start]
                
                # Si la variable termina en este mismo run
                if end_pos <= run_end:
                    suffix = run.text[end_pos - run_start:]
                    run.text = prefix + replacement + suffix
                    return
                else:
                    # La variable continúa en otros runs
                    run.text = prefix + replacement
            
            # Caso 2: Este run está COMPLETAMENTE dentro de la variable
            elif first_run_found and run_start >= start_pos and run_end <= end_pos:
                run.text = ''
            
            # Caso 3: Este run contiene el FINAL de la variable
            elif first_run_found and run_start < end_pos <= run_end:
                suffix = run.text[end_pos - run_start:]
                run.text = suffix
                return
            
            # Si ya pasamos el end_pos, podemos salir
            elif first_run_found and run_start >= end_pos:
                return
            
            current_pos = run_end


def replace_variables_in_template(template_path: str, variables: Dict[str, str]) -> Document:
    """
    Función helper para reemplazar variables en una plantilla.
    """
    return VariableReplacer.replace_in_document(template_path, variables)
