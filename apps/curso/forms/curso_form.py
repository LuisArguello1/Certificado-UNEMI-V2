from apps.core.forms.base_form import CoreBaseModelForm
from django import forms
from ..models import Curso, PlantillaCertificado

class CursoForm(CoreBaseModelForm):
    """
    Formulario para crear/editar cursos.
    """
    class Meta:
        model = Curso
        fields = ['nombre', 'descripcion', 'estado', 'archivo_estudiantes', 'plantilla_certificado']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el campo archivo sea requerido al crear
        if not self.instance.pk:
            self.fields['archivo_estudiantes'].required = True

class PlantillaCertificadoForm(CoreBaseModelForm):
    """
    Formulario para gestionar plantillas.
    """
    class Meta:
        model = PlantillaCertificado
        fields = ['nombre', 'archivo', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }
