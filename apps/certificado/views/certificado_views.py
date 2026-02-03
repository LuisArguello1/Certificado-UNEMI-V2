"""
Vistas para el sistema de certificados.
"""

import json
import logging
import io
import zipfile
import os 

from django.views.generic import TemplateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.urls import reverse

from ..models import ProcesamientoLote, Certificado, VariantePlantilla, Evento, Estudiante, EmailDailyLimit
from ..forms import EventoForm, ExcelUploadForm
from ..services import CertificadoService
from ..utils import parse_excel_estudiantes
from ..tasks import generate_certificate_task
from .catalogo_views import BaseCatalogoMixin
import logging


logger = logging.getLogger(__name__)


class CertificadoCreateView(LoginRequiredMixin, TemplateView):
    """
    Vista para crear evento y generar certificados masivamente.
    """
    template_name = 'certificado/certificado/certificado_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento_form'] = EventoForm()
        context['excel_form'] = ExcelUploadForm()
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Paso 1: Crea el evento y la nómina de estudiantes.
        Redirige al detalle para edición y generación.
        """
        evento_form = EventoForm(request.POST)
        excel_form = ExcelUploadForm(request.POST, request.FILES)
        
        if evento_form.is_valid() and excel_form.is_valid():
            try:
                evento = CertificadoService.create_event_with_students(
                    evento_data=evento_form.cleaned_data,
                    excel_file=request.FILES['archivo_excel'],
                    user=request.user
                )
                
                messages.success(
                    request,
                    f'Evento "{evento.nombre_evento}" creado con éxito. Ahora puede revisar la nómina.'
                )
                
                return redirect('certificado:evento_detail', pk=evento.id)
                
            except Exception as e:
                messages.error(request, f'Error al crear el evento: {str(e)}')
        
        else:
            # Mostrar errores de formularios vía messages
            if excel_form.errors:
                for field, errors in excel_form.errors.items():
                    error_msg = "\n".join(errors)
                    # Limpiar el mensaje si viene del parser que ya trae saltos de línea
                    if field == 'archivo_excel':
                         messages.error(request, f"{error_msg}")
                    else:
                         messages.error(request, f"Error en {field}: {error_msg}")
            
            if evento_form.errors:
                 messages.error(request, "Por favor corrija los errores en el formulario del evento.")

        return self.render_to_response(self.get_context_data(
            evento_form=evento_form,
            excel_form=excel_form
        ))


class CertificadoPreviewView(LoginRequiredMixin, View):
    """
    Vista API para previsualizar la carga de estudiantes desde Excel.
    Valida el formato, cuenta los registros y verifica el límite de correos.
    """
    def post(self, request, *args, **kwargs):
        try:
            if 'archivo_excel' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'No se proporcionó ningún archivo Excel.'}, status=400)
            
            archivo = request.FILES['archivo_excel']
            
            # 1. Parsear Excel (usando la misma utilidad que el servicio)
            try:
                estudiantes_data = parse_excel_estudiantes(archivo)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error al leer Excel: {str(e)}'}, status=400)
            
            num_estudiantes = len(estudiantes_data)
            
            if num_estudiantes == 0:
                return JsonResponse({
                    'success': False, 
                    'error': 'El archivo Excel no contiene estudiantes válidos o está vacío.'
                }, status=400)
            
            # 2. Verificar límite diario de emails
            puede_enviar, restantes, mensaje = EmailDailyLimit.puede_enviar_lote(num_estudiantes)
            
            # Obtener límite configurado para mostrar al usuario
            limite_diario = EmailDailyLimit.get_limit()
            usados_hoy = EmailDailyLimit.get_usage()
            
            return JsonResponse({
                'success': True,
                'estudiantes': estudiantes_data,  # Lista de dicts {nombres_completos, correo_electronico}
                'total_estudiantes': num_estudiantes,
                'email_limit_check': {
                    'puede_enviar': puede_enviar,
                    'limite_diario': limite_diario,
                    'usados_hoy': usados_hoy,
                    'restantes': restantes,
                    'mensaje': mensaje
                }
            })
            
        except Exception as e:
            logger.error(f"Error en preview de certificados: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)


class ProcesamientoStatusView(LoginRequiredMixin, View):
    """
    Vista de estado heredada. Redirige al nuevo detalle del evento.
    """
    def get(self, request, *args, **kwargs):
        try:
            lote = ProcesamientoLote.objects.get(pk=kwargs['pk'])
            return redirect('certificado:evento_detail', pk=lote.evento.id)
        except ProcesamientoLote.DoesNotExist:
            messages.error(request, "El lote de procesamiento no existe.")
            return redirect('certificado:lista')


class CertificadoListView(LoginRequiredMixin, BaseCatalogoMixin, ListView):
    """
    Vista de lista de Eventos de Certificación.
    """
    model = Evento
    template_name = 'certificado/certificado/certificado_list.html'
    context_object_name = 'eventos'
    paginate_by = 15
    titulo = 'Historial de Eventos'
    
    def get_queryset(self):
        from django.db.models import Count
        qs = super().get_queryset().select_related(
            'direccion', 'modalidad'
        ).annotate(
            num_estudiantes=Count('estudiantes')
        ).order_by('-created_at')
        
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [{'name': 'Historial de Eventos'}]
        return context


class EventoDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle de un Evento (post-procesamiento).
    Muestra estadísticas y lista de certificados.
    Permite edición de estudiantes y control del procesamiento.
    """
    model = Evento
    template_name = 'certificado/certificado/evento_detail.html'
    context_object_name = 'evento'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estudiantes con sus certificados (si existen)
        from django.core.paginator import Paginator
        
        # Estudiantes con sus certificados (si existen)
        estudiantes_qs = Estudiante.objects.filter(
            evento=self.object
        ).prefetch_related('certificados').order_by('nombres_completos')
        
        # Paginación (20 por página para mejorar performance)
        page_number = self.request.GET.get('page')
        paginator = Paginator(estudiantes_qs, 20)
        estudiantes_page = paginator.get_page(page_number)
        
        context['estudiantes'] = estudiantes_page
        
        # Procesamiento actual
        context['lote'] = ProcesamientoLote.objects.filter(evento=self.object).first()
        
        # Estadísticas basadas en certificados
        certificados_qs = Certificado.objects.filter(estudiante__evento=self.object)
        total_estudiantes = estudiantes_qs.count()
        enviados = certificados_qs.filter(estado='sent').count()
        exitosos = certificados_qs.filter(estado__in=['sent', 'completed']).count()
        fallidos = certificados_qs.filter(estado='failed').count()
        
        context['stats'] = {
            'total': total_estudiantes,
            'enviados': enviados,
            'exitosos': exitosos,
            'fallidos': fallidos
        }
        
        return context

    def get(self, request, *args, **kwargs):
        # Manejar descarga ZIP si viene el parámetro
        if request.GET.get('download') == 'zip':
            return self.download_zip()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Maneja acciones AJAX para el evento.
        Delega a métodos privados según el 'action'.
        """
        self.object = self.get_object()
        action = request.POST.get('action')
        
        handlers = {
            'update_student': self._handle_update_student,
            'delete_student': self._handle_delete_student,
            'generate_individual': self._handle_generate_individual,
            'start_generation': self._handle_start_generation,
            'start_sending': self._handle_start_sending,
            'get_certificate_status': self._handle_get_status,
            'toggle_qr': self._handle_toggle_qr,
            'get_progress': self._handle_get_progress,
            'delete_certificates': self._handle_delete_certificates
        }
        
        handler = handlers.get(action)
        if handler:
            return handler(request)
            
        return JsonResponse({'success': False, 'error': 'Acción no válida'}, status=400)

    # --- Action Handlers ---

    def _handle_delete_certificates(self, request):
        """
        Elimina todos los registros de certificados (y sus archivos físicos) del evento.
        Mantiene los registros de estudiantes para futura regeneración.
        """
        try:
            # Filtrar certificados que tienen archivos o están generados
            certs = Certificado.objects.filter(estudiante__evento=self.object)
            count = certs.count()
            
            if count == 0:
                return JsonResponse({'success': False, 'error': 'No hay certificados para eliminar.'})

            # Eliminar (esto disparará el método delete() del modelo y borrará archivos)
            # Nota: .delete() en QuerySet NO llama al método delete() del modelo individualmente
            # a menos que iteremos. Para garantizar limpieza física:
            deleted_count = 0
            for cert in certs:
                cert.delete()
                deleted_count += 1
            
            # Resetear lote si existe
            lote = ProcesamientoLote.objects.filter(evento=self.object).first()
            if lote:
                lote.procesados = 0
                lote.exitosos = 0
                lote.fallidos = 0
                lote.estado = 'pending'
                lote.save()

            # Intentar limpiar el directorio del evento si quedó vacío
            # Ruta base: settings.CERTIFICADO_STORAGE_PATH / evento_id
            # Nota: Necesitamos importar settings para esto, o construir la ruta
            try:
                from django.conf import settings
                evento_dir = os.path.join(settings.CERTIFICADO_STORAGE_PATH, str(self.object.id))
                if os.path.exists(evento_dir):
                    os.rmdir(evento_dir) # Falla silenciosamente si no está vacío
            except Exception:
                pass

            return JsonResponse({
                'success': True, 
                'message': f'Se eliminaron {deleted_count} certificados y sus archivos asociados.'
            })
        except Exception as e:
            logger.error(f"Error eliminando certificados del evento {self.object.id}: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'}, status=500)

    def _handle_update_student(self, request):
        est_id = request.POST.get('estudiante_id')
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        try:
            estudiante = get_object_or_404(Estudiante, id=est_id, evento=self.object)
            if nombre: estudiante.nombres_completos = nombre
            if correo: estudiante.correo_electronico = correo
            estudiante.save()
            return JsonResponse({'success': True, 'message': 'Estudiante actualizado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def _handle_delete_student(self, request):
        est_id = request.POST.get('estudiante_id')
        try:
            estudiante = get_object_or_404(Estudiante, id=est_id, evento=self.object)
            estudiante.delete()
            return JsonResponse({'success': True, 'message': 'Estudiante eliminado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def _handle_generate_individual(self, request):
        est_id = request.POST.get('estudiante_id')
        try:
            estudiante = get_object_or_404(Estudiante, id=est_id, evento=self.object)
            
            certificado, created = Certificado.objects.get_or_create(
                estudiante=estudiante,
                defaults={'estado': 'pending'}
            )
            
            if not created:
                certificado.estado = 'pending'
                certificado.error_mensaje = ''
                certificado.save()
            
            generate_certificate_task.delay(certificado.id)
            
            return JsonResponse({
                'success': True, 
                'message': 'Generación iniciada',
                'certificado_id': certificado.id
            })
        except Exception as e:
            logger.error(f"Error en generate_individual: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def _handle_start_generation(self, request):
        try:
            lote = CertificadoService.initiate_generation_lote(self.object.id)
            return JsonResponse({
                'success': True, 
                'message': 'Procesamiento iniciado',
                'lote_id': lote.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def _handle_start_sending(self, request):
        try:
            count, message = CertificadoService.initiate_sending_lote(self.object.id)
            return JsonResponse({
                'success': True, 
                'message': message,
                'count': count
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def _handle_get_status(self, request):
        cert_id = request.POST.get('certificado_id')
        try:
            cert = Certificado.objects.get(id=cert_id)
            is_complete = cert.estado in ['completed', 'failed', 'sent']
            return JsonResponse({
                'success': True,
                'status': cert.estado,
                'is_complete': is_complete,
                'error_mensaje': cert.error_mensaje if cert.estado == 'failed' else ''
            })
        except Certificado.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Certificado no encontrado'})

    def _handle_toggle_qr(self, request):
        try:
            incluir = request.POST.get('incluir_qr') == 'true'
            self.object.incluir_qr = incluir
            self.object.save()
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Error toggling QR: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})

    def _handle_get_progress(self, request):
        """
        Obtiene el progreso actual del procesamiento.
        
        OPTIMIZACIÓN: Incluye un hash del estado para permitir al cliente
        detectar si hubo cambios reales y evitar procesamiento innecesario.
        """
        lote = ProcesamientoLote.objects.filter(evento=self.object).first()
        if not lote:
            return JsonResponse({'success': False, 'error': 'No hay procesamiento activo'})
        
        # Generar hash del estado actual para detección de cambios
        import hashlib
        state_str = f"{lote.procesados}-{lote.exitosos}-{lote.fallidos}-{lote.estado}"
        state_hash = hashlib.md5(state_str.encode()).hexdigest()
        
        return JsonResponse({
            'success': True,
            'progress': lote.porcentaje_progreso,
            'status': lote.estado,
            'exitosos': lote.exitosos,
            'fallidos': lote.fallidos,
            'total': lote.total_estudiantes,
            'is_complete': lote.estado in ['completed', 'partial', 'failed'],
            # Nuevos campos para optimización de polling
            'state_hash': state_hash,
            'last_updated': lote.updated_at.isoformat()
        })

    def download_zip(self):
        evento = self.get_object()
        certificados = Certificado.objects.filter(estudiante__evento=evento, estado='completed').exclude(archivo_pdf='')
        
        if not certificados.exists():
            messages.warning(self.request, "No hay certificados generados para descargar.")
            return redirect('certificado:evento_detail', pk=evento.pk)

        buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                for cert in certificados:
                    if cert.archivo_pdf:
                        try:
                            file_path = cert.archivo_pdf.path
                            if os.path.exists(file_path):
                                # Nombre del archivo dentro del ZIP: Nombre_Estudiante.pdf
                                zip_filename = f"{cert.estudiante.nombres_completos.replace(' ', '_')}.pdf"
                                zip_file.write(file_path, zip_filename)
                        except Exception as e:
                            logger.error(f"Error al añadir certificado {cert.id} al ZIP: {str(e)}")
            
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/zip')
            filename = f"Certificados_{evento.nombre_evento.replace(' ', '_')}.zip"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            logger.error(f"Error generando ZIP para evento {evento.id}: {str(e)}")
            messages.error(self.request, "Error al generar el archivo ZIP.")
            return redirect('certificado:evento_detail', pk=evento.pk)


class EventoDeleteView(LoginRequiredMixin, DetailView):
    """
    Vista para eliminar un Evento y TODOS sus datos relacionados.
    
    Cascading deletion logic:
    - Elimina todos los certificados (y sus archivos físicos)
    - Elimina todos los estudiantes
    - Elimina el lote de procesamiento
    - Elimina el directorio del evento
    - Elimina el evento mismo
    """
    model = Evento
    
    def post(self, request, *args, **kwargs):
        """
        Maneja la eliminación completa del evento.
        """
        self.object = self.get_object()
        evento_id = self.object.id
        evento_nombre = self.object.nombre_evento
        
        try:
            # 1. Eliminar todos los certificados (esto disparará el método delete() del modelo)
            certificados = Certificado.objects.filter(estudiante__evento=self.object)
            cert_count = certificados.count()
            
            for cert in certificados:
                cert.delete()  # Esto borrará los archivos físicos
            
            logger.info(f"Eliminados {cert_count} certificados del evento {evento_id}")
            
            # 2. Eliminar todos los estudiantes
            estudiantes = Estudiante.objects.filter(evento=self.object)
            est_count = estudiantes.count()
            estudiantes.delete()
            
            logger.info(f"Eliminados {est_count} estudiantes del evento {evento_id}")
            
            # 3. Eliminar lote de procesamiento si existe
            ProcesamientoLote.objects.filter(evento=self.object).delete()
            
            # 4. Intentar limpiar el directorio del evento
            try:
                from django.conf import settings
                evento_dir = os.path.join(settings.CERTIFICADO_STORAGE_PATH, str(evento_id))
                if os.path.exists(evento_dir):
                    # Intentar eliminar el directorio completo
                    import shutil
                    shutil.rmtree(evento_dir, ignore_errors=True)
                    logger.info(f"Directorio del evento eliminado: {evento_dir}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio del evento {evento_id}: {e}")
            
            # 5. Eliminar el evento
            self.object.delete()
            
            logger.info(f"Evento {evento_id} eliminado completamente")
            
            return JsonResponse({
                'success': True,
                'message': f'Evento "{evento_nombre}" eliminado correctamente con todos sus datos asociados.',
                'redirect_url': reverse('certificado:lista')
            })
            
        except Exception as e:
            logger.error(f"Error eliminando evento {evento_id}: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Error al eliminar el evento: {str(e)}'
            }, status=500)
