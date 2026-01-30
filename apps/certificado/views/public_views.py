from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from ..models import Certificado

class ValidacionCertificadoView(DetailView):
    """
    Vista pública para validar la autenticidad de un certificado mediante su UUID.
    Accesible vía escaneo de QR.
    """
    model = Certificado
    template_name = 'certificado/public/validacion.html'
    context_object_name = 'certificado'
    
    def get_object(self):
        # Busca por uuid_validacion, si no existe lanza 404
        return get_object_or_404(Certificado, uuid_validacion=self.kwargs['uuid'])
