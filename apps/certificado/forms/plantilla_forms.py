"""
Formularios para gestión de plantillas de certificados.

Este módulo contiene los formularios para PlantillaBase y VariantePlantilla,
incluyendo el formset para gestionar variantes inline.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from apps.core.forms.base_form import CoreBaseModelForm
from ..models import PlantillaBase, VariantePlantilla

class PlantillaBaseForm(CoreBaseModelForm):
    """
    Formulario para crear/editar PlantillaBase.
    Valida que solo se acepten archivos .docx
    """
    
    class Meta:
        model = PlantillaBase
        fields = ['direccion', 'nombre', 'archivo', 'descripcion', 'es_activa']
        widgets = {
            'direccion': forms.Select(attrs={
                'class': 'w-full px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500',
                'placeholder': 'Ej: Plantilla Certificado Vinculación 2024'
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'opacity-0 absolute inset-0 w-full h-full cursor-pointer z-10',
                'accept': '.docx',
                'id': 'id_archivo_base'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción opcional de la plantilla...'
            }),
            'es_activa': forms.CheckboxInput(attrs={
                'class': 'rounded text-indigo-600 focus:ring-indigo-500'
            })
        }
        labels = {
            'direccion': 'Dirección/Gestión',
            'nombre': 'Nombre de la Plantilla',
            'archivo': 'Archivo Word (.docx)',
            'descripcion': 'Descripción',
            'es_activa': 'Marcar como plantilla activa'
        }
        help_texts = {
            'archivo': 'Solo se permiten archivos .docx (Máximo 10MB)',
            'es_activa': 'Solo puede haber una plantilla activa por dirección'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si ya existe una instancia (edición) y tiene archivo, el campo no es obligatorio
        if self.instance.pk and self.instance.archivo:
            self.fields['archivo'].required = False
            # Eliminar atributo required del widget si existe
            if 'required' in self.fields['archivo'].widget.attrs:
                del self.fields['archivo'].widget.attrs['required']

    def clean_archivo(self):
        """Validar que el archivo sea .docx y no exceda 10MB"""
        archivo = self.cleaned_data.get('archivo')
        
        if archivo:
            # Validar extensión
            if not archivo.name.lower().endswith('.docx'):
                raise ValidationError(
                    'Solo se permiten archivos con extensión .docx'
                )
            
            # Validar tamaño (10MB = 10 * 1024 * 1024 bytes)
            if archivo.size > 10 * 1024 * 1024:
                raise ValidationError(
                    'El archivo no debe superar los 10MB'
                )
        
        return archivo


class VariantePlantillaForm(CoreBaseModelForm):
    """
    Formulario para crear/editar VariantePlantilla.
    Usado dentro del formset inline.
    """
    
    class Meta:
        model = VariantePlantilla
        fields = ['nombre', 'archivo', 'descripcion', 'orden', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500',
                'placeholder': 'Ej: Con Logo Grande'
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'block w-full text-xs text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-sm file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition-colors',
                'accept': '.docx'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500',
                'rows': 2,
                'placeholder': 'Descripción opcional...'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500',
                'min': '0'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'rounded text-indigo-600 focus:ring-indigo-500'
            })
        }
        labels = {
            'nombre': 'Nombre de la Variante',
            'archivo': 'Archivo Word (.docx)',
            'descripcion': 'Descripción',
            'orden': 'Orden',
            'activo': 'Activa'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si ya existe una instancia (edición) y tiene archivo, el campo no es obligatorio
        if self.instance.pk and self.instance.archivo:
            self.fields['archivo'].required = False
            # Eliminar atributo required del widget si existe
            if 'required' in self.fields['archivo'].widget.attrs:
                del self.fields['archivo'].widget.attrs['required']

    def clean_archivo(self):
        """Validar que el archivo sea .docx y no exceda 10MB"""
        archivo = self.cleaned_data.get('archivo')
        
        if archivo:
            # Validar extensión
            if not archivo.name.lower().endswith('.docx'):
                raise ValidationError(
                    'Solo se permiten archivos con extensión .docx'
                )
            
            # Validar tamaño (10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise ValidationError(
                    'El archivo no debe superar los 10MB'
                )
        
        return archivo


# Formset para gestionar variantes inline
VariantePlantillaFormSet = inlineformset_factory(
    PlantillaBase,
    VariantePlantilla,
    form=VariantePlantillaForm,
    extra=0,  # No mostrar formularios vacíos por defecto
    can_delete=True,  # Permitir eliminar variantes
    min_num=0,  # Mínimo 0 variantes (opcional)
    validate_min=False,
    max_num=10,  # Máximo 10 variantes por plantilla
    validate_max=True
)
