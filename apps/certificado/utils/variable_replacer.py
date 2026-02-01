
"""
Utilidad para el reemplazo de variables en plantillas Word (.docx).

Este módulo maneja la sustitución de marcadores {{VARIABLE}} preservando
el formato original del documento. También aplica reglas de negocio específicas
para el formato de certificados (sangrías, interlineados).
"""

import re
import logging
from typing import Dict, List, Optional, Any
from docx import Document
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx.shared import Pt, Inches
from docx.enum.text import WD_LINE_SPACING

logger = logging.getLogger(__name__)


class CertificadoPostProcessor:
    """
    Maneja las reglas de formato específicas para los certificados de UNEMI.
    Separado del reemplazador genérico para cumplir con SRP.
    """

    @staticmethod
    def apply_rules(doc: Document, variables: Dict[str, str]) -> None:
        """
        Aplica reglas de negocio al documento después del reemplazo.

        Args:
            doc: Documento de python-docx.
            variables: Diccionario de variables usadas en el reemplazo.
        """
        objetivo_value = variables.get('OBJETIVO DEL PROGRAMA', '') or variables.get('OBJETIVO_PROGRAMA', '')
        nombres_value = variables.get('NOMBRES', '')

        def process_container(paragraphs: List[Paragraph]):
            for i, paragraph in enumerate(paragraphs):
                text = paragraph.text.strip()
                if not text:
                    continue

                # 1. Aplicar sangrías al bloque principal del certificado
                if CertificadoPostProcessor._is_certificate_body(text, i, paragraphs):
                    try:
                        paragraph.paragraph_format.left_indent = Inches(1.2)
                        paragraph.paragraph_format.right_indent = Inches(1.2)
                    except Exception as e:
                        logger.warning(f"No se pudo aplicar sangría en párrafo '{text[:20]}...': {e}")

                # 2. Ajustar interlineado del objetivo
                if objetivo_value and objetivo_value[:50] in text:
                    try:
                        paragraph.paragraph_format.line_spacing = Pt(8)
                        paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                        paragraph.paragraph_format.space_after = Pt(0)
                    except Exception as e:
                        logger.warning(f"No se pudo ajustar interlineado del objetivo: {e}")

                # 3. Formato especial para el nombre del estudiante
                if nombres_value and nombres_value in text and len(text) < 100:
                    try:
                        paragraph.paragraph_format.space_before = Pt(24)
                        for run in paragraph.runs:
                            if run.font:
                                run.font.size = Pt(22)
                    except Exception as e:
                        logger.warning(f"No se pudo aplicar formato al nombre: {e}")

        # Procesar items principales
        process_container(doc.paragraphs)

        # Procesar tablas recursivamente
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    process_container(cell.paragraphs)

    @staticmethod
    def _is_certificate_body(text: str, index: int, paragraphs: List[Paragraph]) -> bool:
        """Determina si un párrafo pertenece al cuerpo legal del certificado."""
        keywords = [
            'La Universidad Estatal', 'expide el presente', 'Gestión de Educación',
            'Escuela de Formación', 'días del mes de', 'del mes de', 'año dos mil'
        ]
        
        # Inicio explícito
        if text.startswith('Por su'):
            return True
            
        # Contiene keywords
        if any(k in text for k in keywords):
            return True
            
        # Párrafos de continuación (basado en sangría anterior)
        if index > 0:
            try:
                prev = paragraphs[index - 1]
                prev_left = prev.paragraph_format.left_indent
                # Si el anterior tenía sangría de ~1.2 pulgadas (aprox 1097280 EMUs o valores cercanos)
                # Usamos 0.5 pulgadas como umbral seguro
                if prev_left and prev_left.inches > 0.5:
                    # Excluir firmas
                    if not text.startswith(('Ph.', 'Msc.', 'Ing.', 'Lic.')) and 'Rector' not in text:
                        return True
            except Exception:
                pass
                
        return False


class VariableReplacer:
    """
    Motor de reemplazo de variables en documentos Word.
    Preserva estrictamente el formato original (fuentes, negritas, colores).
    """

    @classmethod
    def process(cls, doc_path: str, variables: Dict[str, str]) -> Document:
        """
        Ejecuta todo el proceso: carga, normalización, reemplazo y post-procesamiento.

        Args:
            doc_path: Ruta al archivo .docx plantilla.
            variables: Diccionario {clave: valor} a reemplazar.

        Returns:
            Documento procesado (listo para guardar).
        """
        try:
            doc = Document(doc_path)
            
            normalized_vars = cls._normalize_variables(variables)
            
            # Reemplazo en cuerpo principal
            cls._replace_in_paragraphs(doc.paragraphs, normalized_vars)
            
            # Reemplazo en tablas
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        cls._replace_in_paragraphs(cell.paragraphs, normalized_vars)
            
            # Reemplazo en headers/footers
            for section in doc.sections:
                cls._replace_in_paragraphs(section.header.paragraphs, normalized_vars)
                cls._replace_in_paragraphs(section.footer.paragraphs, normalized_vars)
                
            # Aplicar reglas de negocio
            CertificadoPostProcessor.apply_rules(doc, normalized_vars)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error crítico procesando plantilla {doc_path}: {e}", exc_info=True)
            raise

    @staticmethod
    def _normalize_variables(variables: Dict[str, str]) -> Dict[str, str]:
        """
        Normaliza claves para soportar variantes con espacios y guiones bajos.
        Ej: 'NOMBRE COMPLETO' -> 'NOMBRE_COMPLETO'.
        """
        result = {}
        for k, v in variables.items():
            key_upper = k.upper()
            result[key_upper] = str(v)
            
            # Crear variantes para facilitar coincidencias
            if ' ' in key_upper:
                result[key_upper.replace(' ', '_')] = str(v)
            elif '_' in key_upper:
                result[key_upper.replace('_', ' ')] = str(v)
        return result

    @classmethod
    def _replace_in_paragraphs(cls, paragraphs: List[Paragraph], variables: Dict[str, str]) -> None:
        """Itera sobre párrafos y delega el reemplazo."""
        for paragraph in paragraphs:
            cls._replace_in_single_paragraph(paragraph, variables)

    @classmethod
    def _replace_in_single_paragraph(cls, paragraph: Paragraph, variables: Dict[str, str]) -> None:
        """
        Busca {{VAR}} en un párrafo y lo reemplaza, manejando runs fragmentados.
        """
        # Optimización: chequeo rápido
        full_text = paragraph.text
        if '{' not in full_text:
            return

        # Regex para encontrar {{CUALQUIER_COSAS}}
        pattern = r'\{\{[A-ZÁÉÍÓÚÑa-záéíóúñ0-9_ ]+\}\}'
        
        # Iteramos hasta que no queden coincidencias (para manejar nesting si hubiera)
        # o, más seguro, buscamos todas y reemplazamos.
        # Dado que modificamos los runs, es mejor hacer una pasada por match.
        
        # Nota: Usamos loop porque al modificar los runs, los índices cambian.
        processed = False
        while True:
            # Reconstruir texto pues los runs cambiaron
            current_text = paragraph.text
            match = re.search(pattern, current_text)
            if not match:
                break
                
            var_placeholder = match.group()
            var_name = var_placeholder[2:-2].strip().upper()
            
            # Resolver valor
            value = cls._resolve_value(var_name, variables)
            if value is None:
                # Si no encontramos valor, rompemos para evitar ciclo infinito
                # O podríamos loguear warning y dejarlo. 
                # Para evitar loop infinito si la var no existe, debemos salir.
                break
                
            # Ejecutar reemplazo a nivel de Run
            cls._replace_run_content(paragraph, match.start(), match.end(), value)
            processed = True
            
            # Safety break para evitar loops infinitos en casos bordes
            if not processed: 
                 break

    @staticmethod
    def _resolve_value(var_name: str, variables: Dict[str, str]) -> Optional[str]:
        """Busca el valor de la variable intentando varias claves."""
        val = variables.get(var_name)
        if val is not None:
            # Transformación específica para NOMBRES (Business Logic ligera)
            if 'NOMBRE' in var_name and 'CURSO' not in var_name and 'EVENTO' not in var_name:
                return val.upper()
            return val
            
        # Intentar variantes
        val = variables.get(var_name.replace(' ', '_'))
        if val is not None: return val
        
        val = variables.get(var_name.replace('_', ' '))
        if val is not None: return val
        
        return None

    @staticmethod
    def _replace_run_content(paragraph: Paragraph, start_idx: int, end_idx: int, replacement: str) -> None:
        """
        Reemplaza el texto en el rango [start_idx, end_idx) distribuyendo
        el cambio en los runs afectados y limpiando los intermedios.
        """
        current_idx = 0
        first_run_index = -1
        
        runs = paragraph.runs
        
        # 1. Identificar runs afectados
        for i, run in enumerate(runs):
            run_len = len(run.text)
            run_end = current_idx + run_len
            
            # Intersección del run con el rango del match
            intersection_start = max(current_idx, start_idx)
            intersection_end = min(run_end, end_idx)
            
            if intersection_start < intersection_end:
                # Este run es parte del match
                
                # Texto local dentro del run
                local_start = intersection_start - current_idx
                local_end = intersection_end - current_idx
                
                head = run.text[:local_start]
                tail = run.text[local_end:]
                
                if first_run_index == -1:
                    # Es el primer run afectado: aquí inyectamos el reemplazo
                    first_run_index = i
                    run.text = head + replacement + tail
                else:
                    # Runs subsiguientes afectados: se vacían parcialmente
                    run.text = head + tail 
            
            current_idx += run_len


def replace_variables_in_template(template_path: str, variables: Dict[str, str]) -> Document:
    """
    Función helper pública para mantener compatibilidad.
    Interfaz simplificada para el VariableReplacer.
    """
    return VariableReplacer.process(template_path, variables)
