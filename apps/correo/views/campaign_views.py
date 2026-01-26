"""
Views para gestionar campañas de correo masivo.
"""
from django.views.generic import CreateView, TemplateView, ListView, DetailView, View, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.core.serializers.json import DjangoJSONEncoder
import json
from ..forms import CampaignForm
from ..models import EmailCampaign
from ..services import EmailCampaignService
from apps.curso.models import Curso

class CreateCampaignView(LoginRequiredMixin, CreateView):
    """
    Vista para crear una nueva campaña seleccionando un Curso.
    Reemplaza la antigua carga de Excel.
    """
    model = EmailCampaign
    form_class = CampaignForm
    template_name = 'correo/create_campaign.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Menu items para el sidebar (Asumimos que existe MenuService)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['breadcrumbs'] = [
            {'name': 'Correo', 'url': reverse('correo:list')},
            {'name': 'Nueva Campaña'}
        ]
        context['page_title'] = 'Nueva Campaña de Correo'
        
        # Preparar cursos con información adicional para el selector visual
        courses_data = []
        for curso in Curso.objects.filter(estado='disponible'):
            # Buscar un certificado de ejemplo (el último generado válido)
            cert_ejemplo = curso.estudiantes.filter(
                certificados__archivo_generado__isnull=False
            ).exclude(
                certificados__archivo_generado=''
            ).values_list('certificados__archivo_generado', flat=True).last()
            
            courses_data.append({
                'id': curso.id,
                'nombre': curso.nombre,
                'estudiantes_count': curso.estudiantes.count(),
                'preview_url': f"/media/{cert_ejemplo}" if cert_ejemplo else None,
                'tiene_certificados': bool(cert_ejemplo)
            })
        
        context['available_courses'] = courses_data
        return context
    
    def form_valid(self, form):
        """
        Procesa el formulario válido.
        No guardamos inmediatamente en BD con save(), usamos el servicio.
        """
        try:
            # Obtener datos limpios
            name = form.cleaned_data['name']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            course = form.cleaned_data['course']
            
            # Debug: Log del mensaje recibido
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"=== DEBUG CAMPAÑA ===")
            logger.info(f"Nombre: {name}")
            logger.info(f"Mensaje recibido (primeros 200 chars): {message[:200] if message else 'VACÍO'}")
            logger.info(f"Longitud del mensaje: {len(message) if message else 0}")
            logger.info(f"====================")
            
            # Validar que el curso tenga estudiantes
            if not course.estudiantes.exists():
                form.add_error('course', 'El curso seleccionado no tiene estudiantes inscritos.')
                return self.form_invalid(form)

            # Usamos el servicio para crear la campaña y los destinatarios
            campaign = EmailCampaignService.create_campaign_from_course(
                name=name,
                subject=subject,
                message=message,
                course_id=course.id
            )
            
            messages.success(self.request, f"Campaña '{name}' creada con {campaign.total_recipients} destinatarios.")
            return redirect('correo:preview', pk=campaign.id)
            
        except Exception as e:
            messages.error(self.request, f"Error al crear la campaña: {str(e)}")
            return self.form_invalid(form)


class EditCampaignView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar una campaña existente (si no ha sido enviada aun).
    """
    model = EmailCampaign
    form_class = CampaignForm
    template_name = 'correo/create_campaign.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError: pass
            
        context['breadcrumbs'] = [
            {'name': 'Correo', 'url': reverse('correo:list')},
            {'name': 'Editar Campaña'}
        ]
        context['page_title'] = 'Editar Campaña'
        
        # Preparar cursos con información adicional para el selector visual
        courses_data = []
        for curso in Curso.objects.filter(estado='disponible'):
            # Buscar un certificado de ejemplo
            cert_ejemplo = curso.estudiantes.filter(
                certificados__archivo_generado__isnull=False
            ).exclude(
                certificados__archivo_generado=''
            ).values_list('certificados__archivo_generado', flat=True).last()
            
            courses_data.append({
                'id': curso.id,
                'nombre': curso.nombre,
                'estudiantes_count': curso.estudiantes.count(),
                'preview_url': f"/media/{cert_ejemplo}" if cert_ejemplo else None,
                'tiene_certificados': bool(cert_ejemplo)
            })
        
        context['available_courses'] = courses_data
        
        return context
        
    def form_valid(self, form):
        # Al editar, simplemente guardamos y redirigimos al preview.
        # No recreamos los recipients a menos que cambie el curso, pero 
        # por simplicidad asumiremos que es solo actualización de textos.
        # Si cambia el curso, deberíamos regenerar recipients.
        
        self.object = form.save(commit=False)
        old_objet = EmailCampaign.objects.get(pk=self.object.pk)
        
        curso_changed = old_objet.course_id != self.object.course_id
        self.object.save()
        
        if curso_changed:
            # Regenerar destinatarios
            EmailCampaignService.regenerate_recipients(self.object)
            messages.info(self.request, "Al cambiar el curso, se han regenerado los destinatarios.")
        
        messages.success(self.request, "Campaña actualizada correctamente.")
        return redirect('correo:preview', pk=self.object.pk)


class PreviewCampaignView(LoginRequiredMixin, DetailView):
    """
    Vista para previsualizar la campaña antes de enviar.
    Ahora carga desde DB (estado draft o processing), no desde sesión.
    """
    model = EmailCampaign
    template_name = 'correo/preview.html'
    context_object_name = 'campaign'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError: pass
            
        context['breadcrumbs'] = [
            {'name': 'Correo', 'url': reverse('correo:list')},
            {'name': 'Previsualización'}
        ]
        context['page_title'] = 'Previsualización de Campaña'
        
        # Mostrar primeros 10 destinatarios como ejemplo en la tabla estática
        all_recipients = self.object.recipients.all()
        context['preview_recipients'] = all_recipients[:10]
        context['total_count'] = all_recipients.count()
        
        # Serializar TODOS los destinatarios para el modal JS
        # Optimizamos query para traer solo lo necesario
        recipients_data = list(all_recipients.values('full_name', 'email', 'status'))
        context['all_recipients_json'] = json.dumps(recipients_data, cls=DjangoJSONEncoder)
        
        return context


class SendCampaignView(LoginRequiredMixin, View):
    """
    Vista para confirmar y enviar la campaña.
    """
    def post(self, request, pk):
        try:
            # Enviar los correos usando el servicio
            send_result = EmailCampaignService.send_campaign(pk)
            
            if send_result['success']:
                messages.success(
                    request,
                    f"Campaña enviada/procesada. "
                    f"Enviados: {send_result['sent']}, Fallidos: {send_result['failed']}"
                )
            else:
                messages.warning(
                    request,
                    f"Campaña completada con errores. "
                    f"Enviados: {send_result['sent']}, Fallidos: {send_result['failed']}"
                )
            
            # Mostrar errores
            for error in send_result['errors'][:5]:
                messages.error(request, error)
            
            return redirect('correo:detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f"Error al enviar la campaña: {str(e)}")
            return redirect('correo:list')


class CampaignListView(LoginRequiredMixin, ListView):
    model = EmailCampaign
    template_name = 'correo/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError: pass
        
        context['breadcrumbs'] = [{'name': 'Correo'}]
        context['page_title'] = 'Historial de Campañas'
        return context


class CampaignDetailView(LoginRequiredMixin, DetailView):
    model = EmailCampaign
    template_name = 'correo/campaign_detail.html'
    context_object_name = 'campaign'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError: pass
        
        context['breadcrumbs'] = [
            {'name': 'Correo', 'url': reverse('correo:list')},
            {'name': self.object.name}
        ]
        context['page_title'] = f'Campaña: {self.object.name}'
        
        recipients = self.object.recipients.all()
        context['total_recipients'] = recipients.count()
        context['sent_recipients'] = recipients.filter(status='sent').count()
        context['failed_recipients'] = recipients.filter(status='failed').count()
        context['pending_recipients'] = recipients.filter(status='pending').count()
        context['recipients'] = recipients
        return context


class RetrySendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            campaign = get_object_or_404(EmailCampaign, pk=pk)
            result = EmailCampaignService.retry_failed_emails(campaign.id)
            
            if result['success']:
                messages.success(request, f"Reintento completado. Enviados: {result['sent']}")
            else:
                messages.error(request, 'Error al reintentar envío.')
            
            return redirect('correo:detail', pk=pk)
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('correo:list')
