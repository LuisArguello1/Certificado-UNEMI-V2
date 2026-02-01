"""
Vistas para gestión de direcciones/gestiones institucionales.

Este módulo implementa el CRUD completo para Direcciones.
Incluye búsqueda, paginación y protección contra eliminación accidental.
"""

import logging
from typing import Any, Dict

from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from apps.certificado.models import Direccion
from apps.certificado.forms.direccion_form import DireccionForm
from apps.certificado.views.catalogo_views import (
    BaseCatalogoMixin, 
    AjaxFormMixin, 
    ToggleActiveGenericView,
    SafeDeleteMixin
)

logger = logging.getLogger(__name__)


class DireccionListView(LoginRequiredMixin, BaseCatalogoMixin, ListView):
    """
    Vista de listado de direcciones con búsqueda y paginación.
    Permite filtrar por nombre o código.
    """
    model = Direccion
    template_name = 'certificado/direccion/direccion_list.html'
    context_object_name = 'direcciones'
    paginate_by = 12
    titulo = 'Direcciones/Gestiones'
    
    def get_queryset(self):
        """
        Retorna QuerySet filtrado por búsqueda (si existe) y ordenado.
        """
        queryset = Direccion.objects.all().order_by('nombre')
        
        # Búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | 
                Q(codigo__icontains=q)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Añade breadcrumbs y query actual al contexto."""
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [{'name': 'Direcciones'}]
        context['q'] = self.request.GET.get('q', '')
        return context


class DireccionDetailView(LoginRequiredMixin, BaseCatalogoMixin, DetailView):
    """
    Vista de detalle de una dirección mostrando sus relaciones.
    """
    model = Direccion
    template_name = 'certificado/direccion/direccion_detail.html'
    context_object_name = 'direccion'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Detalle: {self.object.nombre}'
        context['breadcrumbs'] = [
            {'name': 'Direcciones', 'url': reverse('certificado:direccion_list')},
            {'name': self.object.nombre}
        ]
        # Mostrar plantillas recientes asociadas
        context['plantillas'] = self.object.plantillas_base.all().order_by('-created_at')[:10]
        return context


class DireccionCreateView(LoginRequiredMixin, BaseCatalogoMixin, AjaxFormMixin, CreateView):
    """
    Vista para crear nueva dirección. Soporta AJAX modal.
    """
    model = Direccion
    form_class = DireccionForm
    template_name = 'certificado/direccion/direccion_form.html'
    ajax_template_name = 'certificado/direccion/direccion_form_fields.html'
    success_url = reverse_lazy('certificado:direccion_list')
    titulo = 'Crear Nueva Dirección/Gestión'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'name': 'Direcciones', 'url': reverse('certificado:direccion_list')},
            {'name': 'Crear Dirección'}
        ]
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Dirección "{form.instance.nombre}" creada exitosamente.'
        )
        return super().form_valid(form)


class DireccionUpdateView(LoginRequiredMixin, BaseCatalogoMixin, AjaxFormMixin, UpdateView):
    """
    Vista para editar dirección existente.
    """
    model = Direccion
    form_class = DireccionForm
    template_name = 'certificado/direccion/direccion_form.html'
    ajax_template_name = 'certificado/direccion/direccion_form_fields.html'
    success_url = reverse_lazy('certificado:direccion_list')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar: {self.object.nombre}'
        context['breadcrumbs'] = [
            {'name': 'Direcciones', 'url': reverse('certificado:direccion_list')},
            {'name': 'Editar Dirección'}
        ]
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Dirección "{form.instance.nombre}" actualizada exitosamente.'
        )
        return super().form_valid(form)


class DireccionDeleteView(LoginRequiredMixin, SafeDeleteMixin, BaseCatalogoMixin, DeleteView):
    """
    Vista para eliminar dirección. Utiliza SafeDeleteMixin para prevenir errores de integridad.
    """
    model = Direccion
    template_name = 'certificado/direccion/direccion_confirm_delete.html'
    success_url = reverse_lazy('certificado:direccion_list')
    titulo = 'Eliminar Dirección'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'name': 'Direcciones', 'url': reverse('certificado:direccion_list')},
            {'name': 'Eliminar Dirección'}
        ]
        # Información de impacto
        context['num_plantillas'] = self.object.plantillas_base.count()
        context['num_eventos'] = self.object.eventos.count()
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre = self.object.nombre
        
        # SafeDeleteMixin manejará la excepción si ocurre
        response = super().delete(request, *args, **kwargs)
        
        # Si llegamos aquí es que no saltó ProtectedError exception
        # Verificamos si realmente se borró
        if not Direccion.objects.filter(pk=self.object.pk).exists():
            messages.success(
                self.request,
                f'Dirección "{nombre}" eliminada exitosamente.'
            )
        return response


class DireccionToggleActiveView(ToggleActiveGenericView):
    """
    Vista para activar/desactivar direcciones (AJAX).
    """
    model_class = Direccion
