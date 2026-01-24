"""
Formulario para carga de archivos Excel.
"""
from django import forms
from django.core.exceptions import ValidationError
import os


class ExcelUploadForm(forms.Form):
    """
    Formulario para cargar archivos Excel con información de estudiantes.
    """
    name = forms.CharField(
        max_length=200,
        required=True,
        label='Nombre de la campaña',
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200',
            'placeholder': 'Ej: Certificados Curso Python 2024'
        })
    )
    
    subject = forms.CharField(
        max_length=300,
        required=True,
        label='Asunto del correo',
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200',
            'placeholder': 'Ej: Tu certificado está listo para descargar'
        })
    )
    
    message = forms.CharField(
        required=False,
        label='Mensaje personalizado (opcional)',
        widget=forms.Textarea(attrs={
            'class': 'form-textarea w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring focus:ring-blue-200',
            'rows': 4,
            'placeholder': 'Mensaje adicional que aparecerá en el correo (opcional)'
        })
    )
    
    excel_file = forms.FileField(
        required=True,
        label='Archivo Excel',
        widget=forms.FileInput(attrs={
            'class': 'form-file-input',
            'accept': '.xlsx,.xls'
        })
    )
    
    def clean_name(self):
        """Valida el nombre de la campaña."""
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')
        return name.strip()
    
    def clean_subject(self):
        """Valida el asunto del correo."""
        subject = self.cleaned_data.get('subject')
        if subject and len(subject.strip()) < 5:
            raise ValidationError('El asunto debe tener al menos 5 caracteres.')
        return subject.strip()
    
    def clean_excel_file(self):
        """Valida el archivo Excel."""
        excel_file = self.cleaned_data.get('excel_file')
        
        if not excel_file:
            raise ValidationError('Debe seleccionar un archivo.')
        
        # Validar extensión
        file_name = excel_file.name.lower()
        valid_extensions = ['.xlsx', '.xls']
        
        if not any(file_name.endswith(ext) for ext in valid_extensions):
            raise ValidationError(
                f'Solo se permiten archivos Excel ({", ".join(valid_extensions)}). '
                f'Archivo recibido: {file_name}'
            )
        
        # Validar tamaño (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB en bytes
        if excel_file.size > max_size:
            raise ValidationError(
                f'El archivo es demasiado grande. Tamaño máximo: 10MB. '
                f'Tamaño del archivo: {excel_file.size / (1024*1024):.2f}MB'
            )
        
        return excel_file
