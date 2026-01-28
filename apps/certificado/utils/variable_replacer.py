"""
Reemplazo de variables en documentos Word.

Usa python-docx para reemplazar placeholders {{VARIABLE}} con valores reales.
"""

import re
import logging
from typing import Dict
from docx import Document
from docx.shared import Pt


logger = logging.getLogger(__name__)


class VariableReplacer:
    """
    Clase para reemplazar variables en documentos Word (.docx).
    
    Variables soportadas (formato {{VARIABLE}}):
        {{NOMBRES}}, {{MODALIDAD}}, {{NOMBRE_EVENTO}}, {{DURACION}},
        {{FECHA_INICIO}}, {{FECHA_FIN}}, {{TIPO}}, {{TIPO_EVENTO}},
        {{FECHA_EMISION}}, {{OBJETIVO_PROGRAMA}}, {{CONTENIDO}}
    """
    
    # Regex pattern para detectar variables (incluyendo espacios)
    VARIABLE_PATTERN = re.compile(r'\{\{([A-Z_ ]+)\}\}')
    
    @staticmethod
    def replace_in_document(doc_path: str, variables: Dict[str, str]) -> Document:
        """
        Carga un documento Word y reemplaza todas las variables.
        
        Args:
            doc_path: Ruta al archivo .docx de plantilla
            variables: Diccionario de reemplazos
                Ejemplo: {"NOMBRES": "Juan Pérez", "MODALIDAD": "Virtual", ...}
        
        Returns:
            Objeto Document modificado (listo para guardar)
        
        Ejemplo:
            >>> from apps.certificado.utils.variable_replacer import VariableReplacer
            >>> variables = {
            ...     "NOMBRES": "Juan Pérez",
            ...     "MODALIDAD": "Virtual",
            ...     "NOMBRE_EVENTO": "Taller de Python"
            ... }
            >>> doc = VariableReplacer.replace_in_document('/path/to/template.docx', variables)
            >>> doc.save('/path/to/output.docx')
        """
        try:
            # Cargar documento
            doc = Document(doc_path)
            
            # Normalizar variables (asegurar mayúsculas)
            variables_upper = {k.upper(): v for k, v in variables.items()}
            
            # Reemplazar en párrafos
            VariableReplacer._replace_in_paragraphs(doc.paragraphs, variables_upper)
            
            # Reemplazar en tablas
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        VariableReplacer._replace_in_paragraphs(cell.paragraphs, variables_upper)
            
            # Reemplazar en headers y footers
            for section in doc.sections:
                VariableReplacer._replace_in_paragraphs(section.header.paragraphs, variables_upper)
                VariableReplacer._replace_in_paragraphs(section.footer.paragraphs, variables_upper)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error al reemplazar variables en documento: {str(e)}")
            raise
    
    @staticmethod
    def _replace_in_paragraphs(paragraphs, variables: Dict[str, str]):
        """
        Reemplaza variables en una lista de párrafos.
        
        Args:
            paragraphs: Lista de párrafos de python-docx
            variables: Diccionario de reemplazos
        """
        for paragraph in paragraphs:
            VariableReplacer._replace_in_paragraph(paragraph, variables)
    
    @staticmethod
    def _replace_in_paragraph(paragraph, variables: Dict[str, str]):
        """
        Reemplaza variables en un solo párrafo, preservando el formato por partes
        y aplicando negritas a variables específicas (como el nombre del evento).
        """
        full_text = paragraph.text
        if '{{' not in full_text:
            return

        # Variables que deben ir en NEGRITA
        BOLD_VARIABLES = ['NOMBRE_EVENTO', 'NOMBRE CURSO', 'TIPO_EVENTO', 'TIPO DE EVENTO']
        
        # 1. Guardar propiedades físicas del párrafo
        p_format = paragraph.paragraph_format
        alignment = p_format.alignment
        
        # 2. Guardar formato base del primer run (referencia)
        base_format = {}
        if paragraph.runs:
            r = paragraph.runs[0]
            base_format = {
                'name': r.font.name,
                'size': r.font.size,
                'bold': r.font.bold,
                'italic': r.font.italic,
                'underline': r.font.underline,
                'color': r.font.color.rgb if r.font.color and r.font.color.rgb else None
            }

        # 3. Reemplazo preciso
        # Usamos regex para encontrar placeholders {{...}}
        import re
        parts = re.split(r'(\{\{[A-Z_ ]+\}\})', full_text)
        if len(parts) <= 1:
            return

        # 4. Limpiar runs actuales pero mantener formato de párrafo
        # paragraph.clear() es efectivo pero a veces resetea la alineación si NO está en el estilo
        paragraph.clear()
        
        # 5. Reconstruir runs con los reemplazos
        for part in parts:
            if not part: continue
            
            # Es un placeholder?
            if part.startswith('{{') and part.endswith('}}'):
                var_name = part[2:-2].strip().upper()
                if var_name in variables:
                    val = str(variables[var_name])
                    run = paragraph.add_run(val)
                    
                    if base_format:
                        run.font.name = base_format['name']
                        run.font.size = base_format['size']
                        run.font.italic = base_format['italic']
                        run.font.underline = base_format['underline']
                        if base_format['color']: run.font.color.rgb = base_format['color']
                        
                        # Formato especial por variable
                        if var_name in BOLD_VARIABLES:
                            run.font.bold = True
                        elif var_name == 'NOMBRES':
                            run.font.bold = True
                            run.font.size = Pt(26)  # Nombre grande e impactante
                        else:
                            run.font.bold = base_format['bold']
                else:
                    # Variable no proporcionada, dejar el placeholder
                    run = paragraph.add_run(part)
                    if base_format: run.font.bold = base_format['bold']
            else:
                # Texto normal
                run = paragraph.add_run(part)
                if base_format:
                    run.font.name = base_format['name']
                    run.font.size = base_format['size']
                    run.font.bold = base_format['bold']
                    run.font.italic = base_format['italic']
                    run.font.underline = base_format['underline']
                    if base_format['color']: run.font.color.rgb = base_format['color']

        # 6. APLICAR AJUSTES DE DISEÑO ESPECÍFICOS SEGÚN VARIABLES DETECTADAS
        # Sangrías para el párrafo descriptivo (Participación)
        HAS_DESCRIPTION = any(v in full_text for v in ['NOMBRE_EVENTO', 'NOMBRE CURSO'])
        HAS_OBJECTIVE = any(v in full_text for v in ['OBJETIVO_PROGRAMA', 'OBJETIVO DEL PROGRAMA'])
        
        if HAS_DESCRIPTION:
            # Aumento máximo de sangrías (100pt) para un centrado perfecto del bloque
            paragraph.paragraph_format.left_indent = Pt(80)
            paragraph.paragraph_format.right_indent = Pt(80)
            # Forzar justificado para bloque limpio
            paragraph.alignment = 3 # JUSTIFY

        if HAS_OBJECTIVE or any(v in full_text for v in ['CONTENIDO', 'CONTENIDO DEL PROGRAMA']):
            # Interlineado ultra-compacto (0.8) para descripciones largas de objetivos/contenido
            paragraph.paragraph_format.line_spacing = 0.8
            # Eliminar todos los espacios extra
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)

        # 7. Forzar restauración de la alineación original si no entramos en los casos anteriores
        if not HAS_DESCRIPTION:
            if alignment is not None:
                paragraph.alignment = alignment
            elif paragraph.style and paragraph.style.paragraph_format.alignment is not None:
                paragraph.alignment = paragraph.style.paragraph_format.alignment
    

@staticmethod
def replace_variables_in_template(template_path: str, variables: Dict[str, str]) -> Document:
    """
    Función helper para reemplazar variables en una plantilla.
    
    Args:
        template_path: Ruta al archivo .docx
        variables: Diccionario de variables a reemplazar
    
    Returns:
        Documento modificado
    
    Ejemplo:
        >>> doc = replace_variables_in_template('/path/to/template.docx', {
        ...     "NOMBRES": "Juan Pérez",
        ...     "DURACION": "40 horas"
        ... })
        >>> doc.save('/path/to/output.docx')
    """
    return VariableReplacer.replace_in_document(template_path, variables)
