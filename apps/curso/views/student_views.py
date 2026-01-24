from django.views.generic import TemplateView, View
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, Http404, HttpResponse
from django.contrib import messages
from ..models import Curso, Estudiante, Certificado

class PublicPortalView(TemplateView):
    """
    Vista pública donde los estudiantes ven los cursos disponibles
    o buscan su certificado.
    """
    template_name = 'curso/public/portal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mostrar solo cursos disponibles
        context['cursos'] = Curso.objects.filter(estado='disponible')
        return context

class CertificateSearchView(TemplateView):
    """
    Vista para buscar un certificado dado un curso y una cédula.
    """
    template_name = 'curso/public/search_result.html'

    def get(self, request, *args, **kwargs):
        # Si no hay parámetros, mostramos el portal o error
        curso_id = request.GET.get('curso_id')
        cedula = request.GET.get('cedula')

        if not curso_id or not cedula:
            messages.error(request, 'Por favor seleccione un curso e ingrese su cédula.')
            return render(request, 'curso/public/portal.html', {
                'cursos': Curso.objects.filter(estado='disponible')
            })

        try:
            # Buscar estudiante (Optimized query)
            estudiante = Estudiante.objects.select_related('curso').get(curso_id=curso_id, cedula=cedula)
            
            # Verificar si tiene certificado generado
            # NOTA: Como la generación es un paso que no hemos implementado completo,
            # aquí podríamos simular o generar al vuelo si la plantilla existe.
            # Por simplicidad y robustez, asumiremos que se busca el objeto certificado.
            
            # Si no existe certificado objeto, pero el estudiante sí, podríamos mostar "En proceso"
            # O permitir descarga si la lógica de generación es al vuelo.
            
            certificado = Certificado.objects.filter(estudiante=estudiante).first()
            
            context = {
                'estudiante': estudiante,
                'certificado': certificado,
                'curso': estudiante.curso
            }
            return render(request, self.template_name, context)

        except Estudiante.DoesNotExist:
            messages.error(request, 'No se encontró un estudiante con esa cédula en el curso seleccionado.')
            return render(request, 'curso/public/portal.html', {
                'cursos': Curso.objects.filter(estado='disponible')
            })

class CertificateVerifyView(TemplateView):
    """
    Vista pública para verificar la autenticidad de un certificado vía código QR.
    """
    template_name = 'curso/public/verify_success.html'

    def get(self, request, code):
        certificado = get_object_or_404(Certificado, codigo_verificacion=code)
        
        return render(request, self.template_name, {
            'certificado': certificado,
            'estudiante': certificado.estudiante,
            'curso': certificado.estudiante.curso
        })

class CertificateDownloadView(View):
    """
    Vista para descargar el archivo del certificado.
    """
    def get(self, request, pk):
        certificado = get_object_or_404(Certificado, pk=pk)
        
        if certificado.archivo_generado:
            response = FileResponse(certificado.archivo_generado, as_attachment=True)
            return response
        else:
            raise Http404("El archivo del certificado no está disponible.")
