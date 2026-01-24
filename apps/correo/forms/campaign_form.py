from django import forms
from apps.core.forms.base_form import CoreBaseModelForm
from ..models import EmailCampaign

class CampaignForm(CoreBaseModelForm):
    """
    Formulario para crear/editar campañas de correo.
    """
    class Meta:
        model = EmailCampaign
        fields = ['name', 'course', 'subject', 'message']
        widgets = {
            # Aquí se podría integrar un widget de CKEditor si estuviera instalado,
            # por ahora usamos Textarea normal pero con clases para ser enriquecido en frontend.
            'message': forms.Textarea(attrs={'rows': 10, 'class': 'rich-text-editor'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo cursos disponibles si es necesario
        # self.fields['course'].queryset = Curso.objects.filter(estado='disponible')
