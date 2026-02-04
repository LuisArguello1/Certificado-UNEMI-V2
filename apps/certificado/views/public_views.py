"""
Vistas públicas accesibles sin autenticación.

Estas vistas manejan la validación pública de certificados mediante QR.
"""

from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Model
from apps.certificado.models import Certificado
from django.views.generic import DetailView

class ValidacionCertificadoView(DetailView):
    """
    Vista pública para validar la autenticidad de un certificado.
    
    Esta vista es accesible públicamente (sin login) y se utiliza cuando
    se escanea el código QR impreso en el certificado digital.
    """
    model = Certificado
    template_name = 'certificado/public/validacion.html'
    context_object_name = 'certificado'
    
    def get_object(self, queryset=None) -> Certificado:
        """
        Recupera el certificado basado en el UUID de la URL.
        Optimizado con select_related para cargar todos los datos del evento en una sola consulta.
        """
        if queryset is None:
            queryset = self.get_queryset()
            
        return get_object_or_404(
            queryset.select_related(
                'estudiante', 
                'estudiante__evento', 
                'estudiante__evento__direccion',
                'estudiante__evento__modalidad',
                'estudiante__evento__tipo',
                'estudiante__evento__tipo_evento'
            ), 
            uuid_validacion=self.kwargs['uuid']
        )
