"""
Vistas para el sistema de certificados.
"""

import json
import logging
import io
import zipfile
import os # Added for os.path.exists

from django.views.generic import TemplateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404 # Added get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse # Added HttpResponse
from django.views import View
from ..models import ProcesamientoLote, Certificado, VariantePlantilla, Evento, Estudiante, EmailDailyLimit # Added Estudiante
from ..forms import EventoForm, ExcelUploadForm
from ..services import CertificadoService
from ..utils import parse_excel_estudiantes
from ..tasks import generate_certificate_task # Added generate_certificate_task
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


class CertificadoListView(LoginRequiredMixin, ListView):
    """
    Vista de lista de Eventos de Certificación.
    """
    model = Evento
    template_name = 'certificado/certificado/certificado_list.html'
    context_object_name = 'eventos'
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Count
        qs = super().get_queryset().select_related(
            'direccion'
        ).annotate(
            num_estudiantes=Count('estudiantes')
        ).order_by('-created_at')
        
        return qs


def get_variantes_api(request, direccion_id):
    """
    API endpoint para obtener variantes de plantilla por dirección.
    Usado por AJAX en el formulario.
    
    Args:
        request: HttpRequest
        direccion_id: ID de la dirección
    
    Returns:
        JsonResponse con variantes disponibles
    """
    try:
        variantes = VariantePlantilla.objects.filter(
            plantilla_base__direccion_id=direccion_id,
            plantilla_base__es_activa=True,
            activo=True
        ).select_related('plantilla_base').order_by('orden', 'nombre')
        
        variantes_data = [
            {
                'id': v.id,
                'nombre': v.nombre,
                'descripcion': v.descripcion
            }
            for v in variantes
        ]
        
        return JsonResponse({
            'success': True,
            'variantes': variantes_data
        })
        
    except Exception as e:
        logger.error(f"Error al obtener variantes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_plantillas_api(request, direccion_id):
    """
    API endpoint para obtener plantilla base y sus variantes por dirección.
    Usado para el modal de selección de plantillas.
    
    Args:
        request: HttpRequest
        direccion_id: ID de la dirección
    
    Returns:
        JsonResponse con:
        - plantilla_base: {id, nombre}
        - variantes: [{id, nombre, descripcion}]
    """
    try:
        from ..models import PlantillaBase
        
        # Buscar plantilla base activa para la dirección
        plantilla_base = PlantillaBase.objects.filter(
            direccion_id=direccion_id,
            es_activa=True
        ).first()
        
        if not plantilla_base:
            return JsonResponse({
                'success': True,
                'plantilla_base': None,
                'variantes': []
            })
            
        # Buscar variantes activas
        variantes = VariantePlantilla.objects.filter(
            plantilla_base=plantilla_base,
            activo=True
        ).order_by('orden', 'nombre')
        
        variantes_data = [
            {
                'id': v.id,
                'nombre': v.nombre,
                'descripcion': v.descripcion
            }
            for v in variantes
        ]
        
        return JsonResponse({
            'success': True,
            'plantilla_base': {
                'id': plantilla_base.id,
                'nombre': plantilla_base.nombre,
                'descripcion': plantilla_base.descripcion
            },
            'variantes': variantes_data
        })
        
    except Exception as e:
        logger.error(f"Error al obtener plantillas: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
        estudiantes = Estudiante.objects.filter(
            evento=self.object
        ).prefetch_related('certificados').order_by('nombres_completos')
        
        context['estudiantes'] = estudiantes
        
        # Procesamiento actual
        context['lote'] = ProcesamientoLote.objects.filter(evento=self.object).first()
        
        # Estadísticas basadas en certificados
        certificados_qs = Certificado.objects.filter(evento=self.object)
        total_estudiantes = estudiantes.count()
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
        """
        self.object = self.get_object()
        evento = self.object # Alias for clarity
        action = request.POST.get('action')
        
        if action == 'update_student':
            est_id = request.POST.get('estudiante_id')
            nombre = request.POST.get('nombre')
            correo = request.POST.get('correo')
            try:
                estudiante = get_object_or_404(Estudiante, id=est_id, evento=evento)
                if nombre: estudiante.nombres_completos = nombre
                if correo: estudiante.correo_electronico = correo
                estudiante.save()
                return JsonResponse({'success': True, 'message': 'Estudiante actualizado'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        elif action == 'delete_student':
            est_id = request.POST.get('estudiante_id')
            try:
                estudiante = get_object_or_404(Estudiante, id=est_id, evento=evento)
                # Al borrar estudiante, Cascade borrará el Certificado asociado
                estudiante.delete()
                return JsonResponse({'success': True, 'message': 'Estudiante eliminado'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        elif action == 'generate_individual':
            est_id = request.POST.get('estudiante_id')
            try:
                # Obtener estudiante
                estudiante = get_object_or_404(Estudiante, id=est_id, evento=evento)
                
                # Obtener o crear certificado
                certificado, created = Certificado.objects.get_or_create(
                    evento=evento,
                    estudiante=estudiante,
                    defaults={'estado': 'pending'}
                )
                
                # Si ya existía, resetear estado para regenerar
                if not created:
                    certificado.estado = 'pending'
                    certificado.error_mensaje = ''
                    certificado.save()
                    logger.info(f"Regenerando certificado {certificado.id} para estudiante {estudiante.nombres_completos}")
                else:
                    logger.info(f"Creando nuevo certificado para estudiante {estudiante.nombres_completos}")
                
                # Encolar tarea de generación
                generate_certificate_task.delay(certificado.id)
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Generación iniciada',
                    'certificado_id': certificado.id
                })
            except Exception as e:
                logger.error(f"Error en generate_individual: {str(e)}", exc_info=True)
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        elif action == 'start_generation':
            try:
                lote = CertificadoService.initiate_generation_lote(evento.id) # Pass event ID
                return JsonResponse({
                    'success': True, 
                    'message': 'Procesamiento iniciado',
                    'lote_id': lote.id
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        elif action == 'start_sending':
            try:
                count, message = CertificadoService.initiate_sending_lote(evento.id) # Pass event ID
                return JsonResponse({
                    'success': True, 
                    'message': message,
                    'count': count
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        elif action == 'get_certificate_status':
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

        elif action == 'toggle_qr':
            try:
                incluir = request.POST.get('incluir_qr') == 'true'
                evento.incluir_qr = incluir
                evento.save()
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error(f"Error toggling QR: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)})

        elif action == 'get_progress':
            lote = ProcesamientoLote.objects.filter(evento=evento).first()
            if not lote:
                return JsonResponse({'success': False, 'error': 'No hay procesamiento activo'})
                
            return JsonResponse({
                'success': True,
                'progress': lote.porcentaje_progreso,
                'status': lote.estado,
                'exitosos': lote.exitosos,
                'fallidos': lote.fallidos,
                'total': lote.total_estudiantes,
                'is_complete': lote.estado in ['completed', 'partial', 'failed']
            })
            
        return JsonResponse({'success': False, 'error': 'Acción no válida'}, status=400)

    def download_zip(self):
        evento = self.get_object()
        certificados = Certificado.objects.filter(evento=evento, estado='completed').exclude(archivo_pdf='')
        
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

