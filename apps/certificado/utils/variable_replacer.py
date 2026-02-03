
"""
Utilidad para el reemplazo de variables en plantillas Word (.docx).

Este módulo maneja la sustitución de marcadores {{VARIABLE}} preservando
el formato original del documento. También aplica reglas de negocio específicas
para el formato de certificados (sangrías, interlineados).

Soporta:
    - Texto plano para variables normales
    - HTML enriquecido para campos específicos (OBJETIVO_PROGRAMA, CONTENIDO)
"""

import re
import logging
from typing import Dict, List, Optional, Any, Set
from docx import Document
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx.shared import Pt, Inches
from docx.enum.text import WD_LINE_SPACING

logger = logging.getLogger(__name__)

# Variables que soportan contenido HTML enriquecido
# IMPORTANTE: Estas deben coincidir EXACTAMENTE con las variables en template_service.py
HTML_ENABLED_VARIABLES: Set[str] = {
    'OBJETIVO DEL PROGRAMA',  # ← Variable exacta usada en template_service
    'CONTENIDO',              # ← Variable exacta usada en template_service
    # Variantes alternativas por compatibilidad
    'OBJETIVO_PROGRAMA',
    'OBJETIVO',
    'CONTENIDO_PROGRAMA',
    'CONTENIDO DEL PROGRAMA'
}


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
        contenido_value = variables.get('CONTENIDO', '') or variables.get('CONTENIDO_PROGRAMA', '')
        nombres_value = variables.get('NOMBRES', '')

        def process_main_body(paragraphs: List[Paragraph]):
            """Procesa solo el cuerpo principal del certificado (primera página)."""
            for i, paragraph in enumerate(paragraphs):
                text = paragraph.text.strip()
                if not text:
                    continue

                # Excluir párrafos que contienen OBJETIVO o CONTENIDO (están en tablas/otra sección)
                if objetivo_value and len(objetivo_value) > 20 and objetivo_value[:30] in text:
                    continue
                if contenido_value and len(contenido_value) > 20 and contenido_value[:30] in text:
                    continue

                # 1. Aplicar sangrías al bloque principal del certificado
                if CertificadoPostProcessor._is_certificate_body(text, i, paragraphs):
                    try:
                        paragraph.paragraph_format.left_indent = Inches(1.2)
                        paragraph.paragraph_format.right_indent = Inches(1.2)
                    except Exception as e:
                        logger.warning(f"No se pudo aplicar sangría en párrafo '{text[:20]}...': {e}")

                # 2. Formato especial para el nombre del estudiante
                if nombres_value and nombres_value in text and len(text) < 100:
                    try:
                        paragraph.paragraph_format.space_before = Pt(24)
                        for run in paragraph.runs:
                            if run.font:
                                run.font.size = Pt(22)
                    except Exception as e:
                        logger.warning(f"No se pudo aplicar formato al nombre: {e}")

        # SOLO procesar el cuerpo principal del documento (NO las tablas)
        # Las tablas contienen OBJETIVO y CONTENIDO que no deben tener sangrías
        process_main_body(doc.paragraphs)
        
        # Limpiar sangrías de las tablas (para evitar herencia de formato)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        try:
                            # Remover sangrías que pudieran haberse aplicado o heredado
                            paragraph.paragraph_format.left_indent = None
                            paragraph.paragraph_format.right_indent = None
                        except Exception as e:
                            pass  # Silenciar errores de formato

    @staticmethod
    def _is_certificate_body(text: str, index: int, paragraphs: List[Paragraph]) -> bool:
        """Determina si un párrafo pertenece al cuerpo legal del certificado."""
        # Palabras clave que NO deben tener sangrías (títulos de secciones)
        excluded_keywords = [
            'Objetivo del programa', 'OBJETIVO', 'Contenido del programa', 'CONTENIDO',
            'Modalidad', 'MODALIDAD'
        ]
        
        # Si el texto es un título de sección, NO aplicar sangrías
        if any(keyword.lower() in text.lower() for keyword in excluded_keywords):
            return False
        
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
        # PERO solo si no es texto muy largo (que probablemente esté en tabla)
        if index > 0 and len(text) < 300:  # Limitar a textos cortos
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
    
    Soporta:
        - Texto plano para variables estándar
        - HTML enriquecido para OBJETIVO_PROGRAMA y CONTENIDO
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
            cls._replace_in_paragraphs(doc.paragraphs, normalized_vars, doc)
            
            # Reemplazo en tablas
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        cls._replace_in_paragraphs(cell.paragraphs, normalized_vars, doc)
            
            # Reemplazo en headers/footers
            for section in doc.sections:
                cls._replace_in_paragraphs(section.header.paragraphs, normalized_vars, doc)
                cls._replace_in_paragraphs(section.footer.paragraphs, normalized_vars, doc)
                
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
    def _replace_in_paragraphs(cls, paragraphs: List[Paragraph], variables: Dict[str, str], document: Document = None) -> None:
        """
        Itera sobre párrafos y delega el reemplazo.
        
        Args:
            paragraphs: Lista de párrafos a procesar.
            variables: Variables a reemplazar.
            document: Documento padre (necesario para crear párrafos/tablas en HTML).
        """
        for paragraph in paragraphs:
            cls._replace_in_single_paragraph(paragraph, variables, document)

    @classmethod
    def _replace_in_single_paragraph(cls, paragraph: Paragraph, variables: Dict[str, str], document: Document = None) -> None:
        """
        Busca {{VAR}} en un párrafo y lo reemplaza, manejando runs fragmentados.
        
        Args:
            paragraph: Párrafo a procesar.
            variables: Variables a reemplazar.
            document: Documento padre (para conversión HTML).
        """
        # Optimización: chequeo rápido
        full_text = paragraph.text
        if '{' not in full_text:
            return

        # Regex para encontrar {{CUALQUIER_COSAS}}
        pattern = r'\{\{[A-ZÁÉÍÓÚÑa-záéíóúñ0-9_ ]+\}\}'
        
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
                break
            
            # Detectar si es una variable HTML
            if cls._is_html_variable(var_name) and cls._contains_html_tags(value):
                # Reemplazo con conversión HTML → Word
                cls._replace_with_html(paragraph, match.start(), match.end(), value, document)
            else:
                # Reemplazo tradicional (texto plano)
                cls._replace_run_content(paragraph, match.start(), match.end(), value)
            
            processed = True
            
            # Safety break para evitar loops infinitos en casos bordes
            if not processed: 
                 break
    
    @staticmethod
    def _is_html_variable(var_name: str) -> bool:
        """Verifica si una variable soporta HTML enriquecido."""
        return var_name.upper() in HTML_ENABLED_VARIABLES
    
    @staticmethod
    def _contains_html_tags(content: str) -> bool:
        """Detecta si el contenido tiene tags HTML."""
        if not content:
            return False
        
        # Buscar tags HTML comunes
        html_pattern = r'<(p|br|strong|b|em|i|u|ul|ol|li|table|tr|td|th|div|span)[>\s]'
        return bool(re.search(html_pattern, content, re.IGNORECASE))
    
    @staticmethod
    def _replace_with_html(paragraph: Paragraph, start_idx: int, end_idx: int, html_content: str, document: Document) -> None:
        """
        Reemplaza el marcador con contenido HTML convertido a Word.
        
        Args:
            paragraph: Párrafo que contiene la variable.
            start_idx: Índice de inicio del marcador.
            end_idx: Índice de fin del marcador.
            html_content: Contenido HTML a insertar.
            document: Documento padre.
        """
        try:
            # Importar el conversor
            from ..services.html_to_word_converter import HTMLToWordConverter
            
            # Limpiar el marcador del párrafo actual
            current_idx = 0
            for run in paragraph.runs:
                run_len = len(run.text)
                run_end = current_idx + run_len
                
                intersection_start = max(current_idx, start_idx)
                intersection_end = min(run_end, end_idx)
                
                if intersection_start < intersection_end:
                    local_start = intersection_start - current_idx
                    local_end = intersection_end - current_idx
                    
                    head = run.text[:local_start]
                    tail = run.text[local_end:]
                    run.text = head + tail
                
                current_idx += run_len
            
            # Convertir HTML a Word e insertar (pasar document para tablas nativas)
            converter = HTMLToWordConverter()
            converter.convert_and_insert(html_content, paragraph, clear_paragraph=False, document=document)
            
        except Exception as e:
            logger.error(f"Error al convertir HTML a Word: {e}", exc_info=True)
            # Fallback: insertar como texto plano
            VariableReplacer._replace_run_content(paragraph, start_idx, end_idx, html_content)

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
