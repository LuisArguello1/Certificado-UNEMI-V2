"""
Formulario para crear eventos y generar certificados.

Hereda de CoreBaseForm para estilos Tailwind automáticos.
"""

from django import forms
from django.core.exceptions import ValidationError
from apps.core.forms.base_form import CoreBaseForm
from ..models import Direccion, VariantePlantilla, Modalidad, Tipo, TipoEvento, PlantillaBase


class EventoForm(CoreBaseForm):
    """
    Formulario para capturar información del evento.
    Incluye todos los campos necesarios para reemplazar variables en certificados.
    """
    
    # Campos
    direccion_gestion = forms.ModelChoiceField(
        queryset=Direccion.objects.filter(activo=True),
        empty_label='-- Seleccione dirección/gestión --',
        label='Dirección/Gestión',
        widget=forms.Select(attrs={
            'id': 'id_direccion_gestion',
            'class': 'hidden', # Se controla vía Modal/JS
        })
    )
    
    plantilla_seleccionada = forms.ModelChoiceField(
        queryset=VariantePlantilla.objects.all(), # Se filtra por JS
        required=False,
        label='Plantilla',
        widget=forms.HiddenInput(attrs={'id': 'id_plantilla_seleccionada'})
    )
    
    modalidad = forms.ModelChoiceField(
        queryset=Modalidad.objects.filter(activo=True),
        empty_label='-- Seleccione modalidad --',
        label='Modalidad',
        widget=forms.Select(attrs={
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    nombre_evento = forms.CharField(
        max_length=300,
        label='Nombre del Evento',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Taller de Python Avanzado',
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    duracion_horas = forms.CharField(
        label='Duración',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: 40 horas',
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    fecha_inicio = forms.DateField(
        label='Fecha de Inicio',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    fecha_fin = forms.DateField(
        label='Fecha de Fin',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    tipo = forms.ModelChoiceField(
        queryset=Tipo.objects.filter(activo=True),
        empty_label='-- Seleccione tipo --',
        label='Tipo',
        widget=forms.Select(attrs={
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    tipo_evento = forms.ModelChoiceField(
        queryset=TipoEvento.objects.filter(activo=True),
        empty_label='-- Seleccione tipo de evento --',
        label='Tipo de Evento',
        widget=forms.Select(attrs={
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    fecha_emision = forms.DateField(
        label='Fecha de Emisión',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    objetivo_programa = forms.CharField(
        label='Objetivo del Programa',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Describa el objetivo principal...',
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500 ckeditor-target',
            'data-editor-type': 'objetivo'
        }),
        help_text='Puede usar formato enriquecido (negritas, cursivas, listas, tablas)'
    )
    
    contenido_programa = forms.CharField(
        label='Contenido del Programa',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Describa el contenido resumido...',
            'class': 'w-full text-xs border-gray-300 rounded-sm focus:border-indigo-500 focus:ring-indigo-500 ckeditor-target',
            'data-editor-type': 'contenido'
        }),
        help_text='Puede usar formato enriquecido (negritas, cursivas, listas, tablas)'
    )
    
    def __init__(self, *args, **kwargs):
        """
        Inicialización personalizada.
        Actualiza queryset de variantes si se proporciona direccion_gestion.
        """
        super().__init__(*args, **kwargs)
        
        # Cargar direcciones activas
        self.fields['direccion_gestion'].queryset = Direccion.objects.filter(activo=True).order_by('codigo')
        
        # Si hay initial data con dirección, pre-cargar variantes
        if 'direccion_gestion' in self.initial and self.initial['direccion_gestion']:
            try:
                direccion_id = self.initial['direccion_gestion']
                # Obtener plantilla base activa de esta dirección
                plantilla_base = PlantillaBase.objects.filter(
                    direccion_id=direccion_id,
                    es_activa=True
                ).first()
                
                if plantilla_base:
                    # Cargar variantes activas de esta plantilla (Optimizado con select_related)
                    self.fields['plantilla_seleccionada'].queryset = VariantePlantilla.objects.filter(
                        plantilla_base=plantilla_base,
                        activo=True
                    ).select_related('plantilla_base').order_by('orden', 'nombre')
            except (ValueError, TypeError):
                pass
        
        # Si hay instancia (edición) - Verificación segura para evitar AttributeError en forms.Form
        instance = getattr(self, 'instance', None)
        if instance and instance.pk and hasattr(instance, 'direccion'):
            self.fields['plantilla_seleccionada'].queryset = VariantePlantilla.objects.filter(
                plantilla_base__direccion=instance.direccion,
                plantilla_base__es_activa=True,
                activo=True
            ).select_related('plantilla_base').order_by('orden', 'nombre')
    
    def clean(self):
        """
        Validaciones cross-field.
        """
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        fecha_emision = cleaned_data.get('fecha_emision')
        direccion_gestion = cleaned_data.get('direccion_gestion')
        
        # Validar fecha_fin >= fecha_inicio
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior o igual a la fecha de inicio.'
                })
        
        # Validar que existe plantilla base para la dirección
        if direccion_gestion:
            from ..models import PlantillaBase
            plantilla_base = PlantillaBase.objects.filter(
                direccion=direccion_gestion,
                es_activa=True
            ).first()
            
            if not plantilla_base:
                raise ValidationError({
                    'direccion_gestion': f'No existe una plantilla base activa para "{direccion_gestion}". '
                                       f'Por favor, configure una plantilla en el admin antes de continuar.'
                })
        
        return cleaned_data
