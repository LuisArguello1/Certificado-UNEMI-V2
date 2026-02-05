"""
Formulario para cargar archivo Excel con estudiantes.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from apps.core.forms.base_form import CoreBaseForm
import openpyxl


class ExcelUploadForm(CoreBaseForm):
    """
    Formulario para cargar archivo Excel con estudiantes.
    
    Formato requerido:
        - Columna 1: NOMBRES COMPLETOS
        - Columna 2: CORREO ELECTRONICO
    """
    
    archivo_excel = forms.FileField(
        label='Archivo Excel (.xlsx, .xls)',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text='Debe contener dos columnas: NOMBRES COMPLETOS, CORREO ELECTRONICO',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'opacity-0 absolute inset-0 w-full h-full cursor-pointer z-10',
        })
    )
    
    def clean_archivo_excel(self):
        """
        Validación del archivo Excel.
        """
        archivo = self.cleaned_data.get('archivo_excel')
        
        if not archivo:
            return archivo
        
        # Validar tamaño (máximo 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if archivo.size > max_size:
            raise ValidationError(
                f'El archivo es demasiado grande ({archivo.size / (1024*1024):.2f}MB). '
                f'Tamaño máximo: 5MB.'
            )
        
        # Validar que se puede abrir y tiene estructura correcta usando el parser unificado
        try:
            from ..utils import parse_excel_estudiantes, ExcelParseError
            
            # El parser leerá el archivo, validará headers y datos
            # Nota: Esto lee todo el archivo en memoria, pero está limitado por el tamaño maximo
            parse_excel_estudiantes(archivo)
            
            # Reiniciar puntero
            archivo.seek(0)
            
        except ExcelParseError as e:
            raise ValidationError(str(e))
        except Exception as e:
            raise ValidationError(
                f'Error al procesar el archivo Excel: {str(e)}'
            )
        
        return archivo
