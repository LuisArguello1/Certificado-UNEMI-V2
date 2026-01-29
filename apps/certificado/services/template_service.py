"""
Servicio para procesar plantillas de certificado.

Carga plantillas Word, inyecta variables y genera documentos.
"""

import os
import logging
from typing import Dict
from docx import Document
from django.conf import settings


logger = logging.getLogger(__name__)


class TemplateService:
    """
    Servicio para procesar plantillas de certificado.
    
    Responsabilidades:
    - Cargar plantillas Word
    - Inyectar variables
    - Generar documentos DOCX
    """
    
    @staticmethod
    def generate_docx(template_path: str, variables: Dict[str, str], output_path: str) -> str:
        """
        Genera un documento DOCX desde una plantilla con variables reemplazadas.
        
        Args:
            template_path: Ruta absoluta a la plantilla .docx
            variables: Diccionario de variables a reemplazar
            output_path: Ruta donde guardar el documento generado
        
        Returns:
            Ruta absoluta del archivo generado
        
        Raises:
            FileNotFoundError: Si la plantilla no existe
            Exception: Si hay error al generar el documento
        
        Ejemplo:
            >>> from apps.certificado.services.template_service import TemplateService
            >>> variables = {
            ...     "NOMBRES": "Juan Pérez",
            ...     "MODALIDAD": "Virtual",
            ...     "NOMBRE_EVENTO": "Taller Python",
            ...     "DURACION": "40 horas"
            ... }
            >>> output = TemplateService.generate_docx(
            ...     '/path/to/template.docx',
            ...     variables,
            ...     '/path/to/output.docx'
            ... )
            >>> print(output)  # /path/to/output.docx
        """
        try:
            # Validar que existe la plantilla
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Plantilla no encontrada: {template_path}")
            
            # Importar utilidad de reemplazo
            from ..utils.variable_replacer import replace_variables_in_template
            
            # Cargar y procesar plantilla
            doc = replace_variables_in_template(template_path, variables)
            
            # Asegurar que existe el directorio de salida
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Guardar documento
            doc.save(output_path)
            
            # Validar que se creó el archivo
            if not os.path.exists(output_path):
                raise Exception(f"El archivo no se generó correctamente: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error al generar DOCX: {str(e)}")
            raise
    
    @staticmethod
    def get_variables_from_evento_estudiante(evento, estudiante) -> Dict[str, str]:
        """
        Construye el diccionario de variables desde un Evento y Estudiante.
        
        Args:
            evento: Instancia del modelo Evento
            estudiante: Instancia del modelo Estudiante
        
        Returns:
            Diccionario con todas las variables universales
        
        Ejemplo:
            >>> evento = Evento.objects.get(id=1)
            >>> estudiante = Estudiante.objects.get(id=1)
            >>> variables = TemplateService.get_variables_from_evento_estudiante(evento, estudiante)
            >>> print(variables)
            {
                'NOMBRES': 'Juan Pérez',
                'MODALIDAD': 'Virtual',
                ...
            }
        """
        # Diccionario para meses en español (Capitalizados para el formato del usuario)
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }

        def format_fecha_es(fecha):
            """Formato completo: 16 de Septiembre de 2025"""
            if not fecha: return ''
            return f"{fecha.day} de {meses[fecha.month]} de {fecha.year}"
        
        def format_fecha_sin_anio(fecha):
            """Formato sin año: 16 de septiembre"""
            if not fecha: return ''
            return f"{fecha.day} de {meses[fecha.month].lower()}"
        
        def format_fecha_con_del(fecha):
            """Formato con 'del': 20 de septiembre del 2025"""
            if not fecha: return ''
            return f"{fecha.day} de {meses[fecha.month].lower()} del {fecha.year}"
        
        def format_fecha_emision_especial(fecha):
            """Formato especial: 30 días del mes de septiembre del 2025"""
            if not fecha: return ''
            return f"{fecha.day} días del mes de {meses[fecha.month].lower()} del {fecha.year}"

        # Formatear fechas con diferentes formatos
        fecha_inicio_str = format_fecha_es(evento.fecha_inicio)
        fecha_fin_str = format_fecha_es(evento.fecha_fin)
        fecha_emision_str = format_fecha_es(evento.fecha_emision)
        
        # Formatos adicionales para las variables con espacio
        fecha_inicio_sin_anio = format_fecha_sin_anio(evento.fecha_inicio)  # "16 de septiembre"
        fecha_fin_con_del = format_fecha_con_del(evento.fecha_fin)  # "20 de septiembre del 2025"
        
        # Partes de la fecha para mayor flexibilidad
        dia_emision = str(evento.fecha_emision.day) if evento.fecha_emision else ''
        mes_emision = meses[evento.fecha_emision.month] if evento.fecha_emision else ''
        anio_emision = str(evento.fecha_emision.year) if evento.fecha_emision else ''
        mes_anio_emision = f"{mes_emision} de {anio_emision}" if evento.fecha_emision else ''
        
        # Construir diccionario con todas las variables universales
        # Nota: No todas las variables estarán en todas las plantillas, y eso está bien
        variables = {
            'NOMBRES': estudiante.nombres_completos.upper(),
            'MODALIDAD': evento.modalidad.nombre if evento.modalidad else '',
            'NOMBRE_EVENTO': evento.nombre_evento,
            'NOMBRE CURSO': evento.nombre_evento,
            'DURACION': f'{evento.duracion_horas}' if evento.duracion_horas else '0',
            'HORAS': f'{evento.duracion_horas}' if evento.duracion_horas else '0',
            # Variables de fecha con guión bajo (formato completo)
            'FECHA_INICIO': fecha_inicio_str,
            'FECHA_FIN': fecha_fin_str,
            # Variables de fecha con espacio (formatos especiales)
            'FECHA INICIO': fecha_inicio_sin_anio,  # "16 de septiembre"
            'FECHA FIN': fecha_fin_con_del,  # "20 de septiembre del 2025"
            # Tipo de evento
            'TIPO': evento.tipo.nombre if evento.tipo else '',
            'TIPO_EVENTO': evento.tipo_evento.nombre if evento.tipo_evento else '',
            'TIPO DE EVENTO': evento.tipo_evento.nombre if evento.tipo_evento else '',
            # Fechas de emisión
            'FECHA_EMISION': fecha_emision_str,
            'FECHA DE EMISION': format_fecha_emision_especial(evento.fecha_emision),  # "30 días del mes de septiembre del 2025"
            'DIA_EMISION': dia_emision,
            'MES_EMISION': mes_emision,
            'ANIO_EMISION': anio_emision,
            'MES_ANIO_EMISION': mes_anio_emision,
            # Contenido del programa
            'OBJETIVO_PROGRAMA': evento.objetivo_programa if evento.objetivo_programa else '',
            'OBJETIVO DEL PROGRAMA': evento.objetivo_programa if evento.objetivo_programa else '',
            'CONTENIDO': evento.contenido_programa if evento.contenido_programa else '',
        }
        
        # Variables construidas
        return variables
