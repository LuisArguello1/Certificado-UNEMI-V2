"""
Vistas para gestión de catálogos (Modalidad, Tipo, TipoEvento).

Este módulo define las vistas CRUD para las entidades básicas del sistema.
Implementa Mixins robustos para manejo de AJAX, borrado seguro y consistencia visual.
"""

import logging
from typing import Any, Dict, Optional, Type

from django.db import models
from django.db.models import ProtectedError
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.certificado.models import Modalidad, Tipo, TipoEvento
from apps.certificado.forms.catalogo_forms import ModalidadForm, TipoForm, TipoEventoForm

logger = logging.getLogger(__name__)


# =============================================================================
# MIXINS
# =============================================================================

class BaseCatalogoMixin:
    """
    Mixin base para proporcionar contexto estándar a las vistas de catálogo.
    Elimina la necesidad de definir get_context_data en cada vista repetitivamente.
    """
    titulo: str = ""
    breadcrumb_name: str = ""
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Inyecta títulos y breadcrumbs al contexto."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.titulo
        if self.breadcrumb_name:
            context['breadcrumb_name'] = self.breadcrumb_name
        return context


class AjaxFormMixin:
    """
    Mixin para manejar formularios vía AJAX.
    Retorna JSON en caso de éxito o HTML parcial en caso de error.
    """
    ajax_template_name: Optional[str] = None

    def form_valid(self, form) -> HttpResponse:
        """Maneja el éxito del formulario (redirección o JSON)."""
        response = super().form_valid(form)
        if self._is_ajax():
            return JsonResponse({
                'success': True,
                'redirect_url': self.success_url
            })
        return response

    def form_invalid(self, form) -> HttpResponse:
        """Maneja errores de validación (HTML parcial para modal o recarga)."""
        if self._is_ajax():
            template = self.ajax_template_name or self.template_name
            context = self.get_context_data(form=form)
            # Renderizar solo el contenido necesario
            html_content = self.render_to_response(context).rendered_content
            return JsonResponse({
                'success': False,
                'html': html_content
            }, safe=False)
        
        return super().form_invalid(form)

    def render_to_response(self, context, **response_kwargs):
        """Usa el template AJAX si la petición lo requiere."""
        if self._is_ajax() and self.ajax_template_name:
            self.template_name = self.ajax_template_name
        return super().render_to_response(context, **response_kwargs)

    def _is_ajax(self) -> bool:
        """Helper para detectar peticiones AJAX."""
        return self.request.headers.get('x-requested-with') == 'XMLHttpRequest'


class SafeDeleteMixin:
    """
    Mixin para proteger la eliminación de registros referenciados.
    Captura `ProtectedError` en `post` o `delete` y muestra un mensaje amigable.
    Compatibilidad mejorada con Django 4.2+ / 5.0+.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Intercepta la solicitud POST para atrapar ProtectedError.
        En Django reciente, delete() se llama dentro de form_valid(), lo que bypass
        la anulación directa de delete() si no se intercepta aquí.
        """
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError as e:
            msg = "No se puede eliminar este registro porque está siendo utilizado por otros elementos (Eventos, Certificados, etc)."
            messages.error(request, msg)
            logger.warning(f"Intento fallido de eliminar {self.get_object()} (ProtectedError): {e}")
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            messages.error(request, f"Error inesperado al eliminar: {str(e)}")
            logger.error(f"Error eliminando {self.get_object()}: {e}", exc_info=True)
            return HttpResponseRedirect(self.success_url)

    def delete(self, request, *args, **kwargs):
        """Backup para versiones antiguas de Django o llamadas directas."""
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError:
            # Si el error ya fue manejado por post (lo cual es raro si llama a super), 
            # esto es redundante pero seguro.
            msg = "No se puede eliminar este registro porque está siendo utilizado."
            messages.error(request, msg)
            return HttpResponseRedirect(self.success_url)


class ToggleActiveGenericView(LoginRequiredMixin, View):
    """
    Vista genérica para cambiar el estado 'activo' de un modelo.
    Espera que la subclase defina `model_class`.
    """
    model_class: Type[models.Model] = None

    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        """Ejecuta el cambio de estado (toggle)."""
        if not self.model_class:
            return JsonResponse({'success': False, 'message': 'Modelo no definido'}, status=500)

        instance = get_object_or_404(self.model_class, pk=pk)
        
        # Toggle
        instance.activo = not instance.activo
        instance.save()
        
        return JsonResponse({
            'success': True, 
            'is_active': instance.activo, 
            'message': 'Estado actualizado correctamente.'
        })


# =============================================================================
# MODALIDAD
# =============================================================================

class ModalidadListView(LoginRequiredMixin, BaseCatalogoMixin, ListView):
    model = Modalidad
    template_name = 'certificado/modalidad/modalidad_list.html'
    context_object_name = 'items'
    paginate_by = 10
    titulo = "Gestión de Modalidades"
    breadcrumb_name = "Modalidades"

    def get_queryset(self):
        return Modalidad.objects.all().order_by('nombre')


class ModalidadCreateView(LoginRequiredMixin, BaseCatalogoMixin, AjaxFormMixin, CreateView):
    model = Modalidad
    form_class = ModalidadForm
    template_name = 'certificado/modalidad/modalidad_form.html'
    ajax_template_name = 'certificado/modalidad/modalidad_form_fields.html'
    success_url = reverse_lazy('certificado:modalidad_list')
    titulo = "Crear Modalidad"

    def form_valid(self, form):
        messages.success(self.request, f'Modalidad "{form.instance.nombre}" creada.')
        return super().form_valid(form)


class ModalidadUpdateView(LoginRequiredMixin, BaseCatalogoMixin, AjaxFormMixin, UpdateView):
    model = Modalidad
    form_class = ModalidadForm
    template_name = 'certificado/modalidad/modalidad_form.html'
    ajax_template_name = 'certificado/modalidad/modalidad_form_fields.html'
    success_url = reverse_lazy('certificado:modalidad_list')
    titulo = "Editar Modalidad"

    def form_valid(self, form):
        messages.success(self.request, f'Modalidad "{form.instance.nombre}" actualizada.')
        return super().form_valid(form)


class ModalidadDeleteView(LoginRequiredMixin, SafeDeleteMixin, BaseCatalogoMixin, DeleteView):
    model = Modalidad
    template_name = 'certificado/modalidad/modalidad_confirm_delete.html'
    success_url = reverse_lazy('certificado:modalidad_list')
    titulo = "Eliminar Modalidad"

    def delete(self, request, *args, **kwargs):
        # Primero obtenemos el objeto para el mensaje de éxito (si procede)
        self.object = self.get_object() 
        response = super().delete(request, *args, **kwargs)
        # Si SafeDeleteMixin captura error, redirige antes de llegar aquí.
        # Si llega aquí es porque fue exitoso (o super().delete retornó redirect).
        # Verificamos si el objeto sigue existiendo para saber si falló
        if not Modalidad.objects.filter(pk=self.object.pk).exists():
           messages.success(self.request, 'Modalidad eliminada exitosamente.')
        return response

class ModalidadToggleActiveView(ToggleActiveGenericView):
    model_class = Modalidad


# =============================================================================
# TIPO
# =============================================================================

class TipoListView(LoginRequiredMixin, BaseCatalogoMixin, ListView):
    model = Tipo
    template_name = 'certificado/tipo/tipo_list.html'
    context_object_name = 'items'
    paginate_by = 10
    titulo = "Gestión de Tipos Generales"

    def get_queryset(self):
        return Tipo.objects.all().order_by('nombre')


class TipoCreateView(LoginRequiredMixin, BaseCatalogoMixin, AjaxFormMixin, CreateView):
    model = Tipo
    form_class = TipoForm
    template_name = 'certificado/tipo/tipo_form.html'
    ajax_template_name = 'certificado/tipo/tipo_form_fields.html'
    success_url = reverse_lazy('certificado:tipo_list')
    titulo = "Crear Tipo General"

    def form_valid(self, form):
        messages.success(self.request, f'Tipo "{form.instance.nombre}" creado.')
        return super().form_valid(form)


class TipoUpdateView(LoginRequiredMixin, BaseCatalogoMixin, AjaxFormMixin, UpdateView):
    model = Tipo
    form_class = TipoForm
    template_name = 'certificado/tipo/tipo_form.html'
    ajax_template_name = 'certificado/tipo/tipo_form_fields.html'
    success_url = reverse_lazy('certificado:tipo_list')
    titulo = "Editar Tipo General"

    def form_valid(self, form):
        messages.success(self.request, f'Tipo "{form.instance.nombre}" actualizado.')
        return super().form_valid(form)


class TipoDeleteView(LoginRequiredMixin, SafeDeleteMixin, BaseCatalogoMixin, DeleteView):
    model = Tipo
    template_name = 'certificado/tipo/tipo_confirm_delete.html'
    success_url = reverse_lazy('certificado:tipo_list')
    titulo = "Eliminar Tipo General"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        if not Tipo.objects.filter(pk=self.object.pk).exists():
            messages.success(self.request, 'Tipo eliminado exitosamente.')
        return response


class TipoToggleActiveView(ToggleActiveGenericView):
    model_class = Tipo


# =============================================================================
# TIPO EVENTO
# =============================================================================


class TipoEventoListView(LoginRequiredMixin, BaseCatalogoMixin, ListView):
    model = TipoEvento
    template_name = 'certificado/tipo_evento/tipo_evento_list.html'
    context_object_name = 'items'
    paginate_by = 10
    titulo = "Gestión de Tipos de Evento"

    def get_queryset(self):
        return TipoEvento.objects.all().order_by('nombre')


class TipoEventoCreateView(LoginRequiredMixin, BaseCatalogoMixin, AjaxFormMixin, CreateView):
    model = TipoEvento
    form_class = TipoEventoForm
    template_name = 'certificado/tipo_evento/tipo_evento_form.html'
    ajax_template_name = 'certificado/tipo_evento/tipo_evento_form_fields.html'
    success_url = reverse_lazy('certificado:tipo_evento_list')
    titulo = "Crear Tipo de Evento"

    def form_valid(self, form):
        messages.success(self.request, f'Tipo de Evento "{form.instance.nombre}" creado.')
        return super().form_valid(form)


class TipoEventoUpdateView(LoginRequiredMixin, BaseCatalogoMixin, AjaxFormMixin, UpdateView):
    model = TipoEvento
    form_class = TipoEventoForm
    template_name = 'certificado/tipo_evento/tipo_evento_form.html'
    ajax_template_name = 'certificado/tipo_evento/tipo_evento_form_fields.html'
    success_url = reverse_lazy('certificado:tipo_evento_list')
    titulo = "Editar Tipo de Evento"

    def form_valid(self, form):
        messages.success(self.request, f'Tipo de Evento "{form.instance.nombre}" actualizado.')
        return super().form_valid(form)


class TipoEventoDeleteView(LoginRequiredMixin, SafeDeleteMixin, BaseCatalogoMixin, DeleteView):
    model = TipoEvento
    template_name = 'certificado/tipo_evento/tipo_evento_confirm_delete.html'
    success_url = reverse_lazy('certificado:tipo_evento_list')
    titulo = "Eliminar Tipo de Evento"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        if not TipoEvento.objects.filter(pk=self.object.pk).exists():
            messages.success(self.request, 'Tipo de Evento eliminado exitosamente.')
        return response


class TipoEventoToggleActiveView(ToggleActiveGenericView):
    model_class = TipoEvento
