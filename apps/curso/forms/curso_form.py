from apps.core.forms.base_form import CoreBaseModelForm
from django import forms
from ..models import Curso, PlantillaCertificado, Estudiante

class CursoForm(CoreBaseModelForm):
    class Meta:
        model = Curso
        fields = [
            'nombre', 'descripcion', 'responsable',
            'fecha_inicio', 'fecha_fin',
            'archivo_estudiantes', 'plantilla_certificado', 'configuracion_certificado'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Breve descripción del curso...'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'configuracion_certificado': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['archivo_estudiantes'].required = True

    def clean(self):
        cleaned_data = super().clean()

        nombre = cleaned_data.get('nombre')
        responsable = cleaned_data.get('responsable')

        if nombre:
            cleaned_data['nombre'] = " ".join(str(nombre).split())

        if responsable:
            cleaned_data['responsable'] = " ".join(str(responsable).split())

        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise forms.ValidationError({
                    'fecha_fin': "La fecha de fin no puede ser anterior a la fecha de inicio."
                })

        return cleaned_data


class PlantillaCertificadoForm(CoreBaseModelForm):
    class Meta:
        model = PlantillaCertificado
        fields = ['nombre', 'archivo', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class CursoCertificateConfigForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['plantilla_certificado', 'configuracion_certificado', 'texto_certificado']
        widgets = {
            'configuracion_certificado': forms.HiddenInput(),
            'texto_certificado': forms.HiddenInput(), # Usamos QuillJS en el template
        }

class EstudianteForm(CoreBaseModelForm):
    class Meta:
        model = Estudiante
        fields = ['nombre_completo', 'cedula', 'correo']
