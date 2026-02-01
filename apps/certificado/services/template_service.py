"""
Servicio para procesar plantillas de certificado.

Gestiona la inyección de variables en plantillas Word (.docx) con un mapeo optimizado
y estricto para maximizar el rendimiento.
"""

import os
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from datetime import date

logger = logging.getLogger(__name__)


class TemplateService:
    """
    Servicio de alto rendimiento para la generación de DOCX.
    """
    
    # Mapeo de meses para formateo en español
    _MONTHS = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }

    @staticmethod
    def generate_docx(template_path: str, variables: Dict[str, str], output_path: str) -> str:
        """
        Genera el documento final reemplazando variables.

        Args:
            template_path (str): Ruta absoluta de la plantilla.
            variables (Dict[str, str]): Diccionario exacto de variables.
            output_path (str): Ruta absoluta de destino.

        Returns:
            str: Ruta del archivo generado.

        Raises:
            FileNotFoundError: Si falta la plantilla.
            RuntimeError: Si falla la generación.
        """
        try:
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Plantilla no encontrada: {template_path}")
            
            # Importación local para evitar ciclos
            from ..utils.variable_replacer import replace_variables_in_template
            
            # Reemplazo de variables (delegado al util especializado)
            doc = replace_variables_in_template(template_path, variables)
            
            # Asegurar directorio y guardar
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            doc.save(output_path)
            
            if not os.path.exists(output_path):
                raise RuntimeError(f"Fallo verificando archivo generado: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generando DOCX: {e}")
            raise

    @classmethod
    def get_variables_from_evento_estudiante(cls, evento: Any, estudiante: Any) -> Dict[str, str]:
        """
        Genera el diccionario de variables optimizado.
        
        Variables Estrictas:
            - TIPO
            - TIPO DE EVENTO
            - NOMBRE CURSO
            - HORAS
            - FECHA INICIO
            - FECHA FIN
            - FECHA DE EMISION
            - OBJETIVO DEL PROGRAMA
            - CONTENIDO
            - MODALIDAD
            - NOMBRES (Requerido para reemplazo de nombre estudiante)

        Args:
            evento: Instancia de Evento.
            estudiante: Instancia de Estudiante.

        Returns:
            Dict[str, str]: Mapeo plano llave-valor.
        """
        
        # 1. Helpers de formateo
        def fmt_date_simple(d: Optional[date]) -> str:
            """Ej: 16 de septiembre"""
            if not d: return ''
            return f"{d.day} de {cls._MONTHS[d.month]}"
        
        def fmt_date_full_del(d: Optional[date]) -> str:
            """Ej: 20 de septiembre del 2025"""
            if not d: return ''
            return f"{d.day} de {cls._MONTHS[d.month]} del {d.year}"
            
        def fmt_date_emission(d: Optional[date]) -> str:
            """Ej: 30 de días del mes de septiembre del 2025"""
            if not d: return ''
            # El formato solicitado suele ser "a los X días del mes..."
            # Ajustamos a lo que el usuario pidió: FECHA DE EMISION
            return f"{d.day} días del mes de {cls._MONTHS[d.month]} del {d.year}"

        # 2. Construcción directa del diccionario
        return {
            # Variable crítica de identidad
            'NOMBRES': estudiante.nombres_completos.upper(),
            
            # Variables de Evento
            'TIPO': evento.tipo.nombre if evento.tipo else '',
            'TIPO DE EVENTO': evento.tipo_evento.nombre if evento.tipo_evento else '',
            'NOMBRE CURSO': evento.nombre_evento or '',
            'HORAS': str(evento.duracion_horas) if evento.duracion_horas else '0',
            'MODALIDAD': evento.modalidad.nombre if evento.modalidad else '',
            
            # Fechas con formatos específicos
            'FECHA INICIO': fmt_date_simple(evento.fecha_inicio),
            'FECHA FIN': fmt_date_full_del(evento.fecha_fin),
            'FECHA DE EMISION': fmt_date_emission(evento.fecha_emision),
            
            # Contenidos largos
            'OBJETIVO DEL PROGRAMA': evento.objetivo_programa or '',
            'CONTENIDO': evento.contenido_programa or '',
        }
