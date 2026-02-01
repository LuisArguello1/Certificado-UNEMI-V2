"""
Vistas para gestión de plantillas de certificados.

Este módulo contiene todas las vistas CRUD para PlantillaBase y VariantePlantilla.
Soporta la carga de archivos DOCX y la gestión de variantes mediante formsets.
"""

import logging
from typing import Any, Dict

from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect

from apps.certificado.models import PlantillaBase
from apps.certificado.forms.plantilla_forms import PlantillaBaseForm, VariantePlantillaFormSet
from apps.certificado.views.catalogo_views import BaseCatalogoMixin

logger = logging.getLogger(__name__)


class PlantillaListView(LoginRequiredMixin, BaseCatalogoMixin, ListView):
    """
    Vista de listado de plantillas base con paginación.
    """
    model = PlantillaBase
    template_name = 'certificado/plantilla/plantilla_list.html'
    context_object_name = 'plantillas'
    paginate_by = 12
    titulo = 'Plantillas de Certificados'
    
    def get_queryset(self):
        """Optimizar query con select_related y prefetch_related"""
        return PlantillaBase.objects.select_related('direccion').prefetch_related('variantes').order_by('-created_at')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [{'name': 'Plantillas de Certificados'}]
        return context


class PlantillaDetailView(LoginRequiredMixin, BaseCatalogoMixin, DetailView):
    """
    Vista de detalle de una plantilla base mostrando todas sus variantes.
    """
    model = PlantillaBase
    template_name = 'certificado/plantilla/plantilla_detail.html'
    context_object_name = 'plantilla'
    
    def get_queryset(self):
        """Optimizar query"""
        return PlantillaBase.objects.select_related('direccion').prefetch_related('variantes')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Detalle: {self.object.nombre}'
        context['breadcrumbs'] = [
            {'name': 'Plantillas', 'url': reverse('certificado:plantilla_list')},
            {'name': self.object.nombre}
        ]
        context['variantes'] = self.object.variantes.filter(activo=True).order_by('orden', 'nombre')
        return context


class PlantillaCreateView(LoginRequiredMixin, BaseCatalogoMixin, CreateView):
    """
    Vista para crear nueva plantilla base con variantes inline.
    """
    model = PlantillaBase
    form_class = PlantillaBaseForm
    template_name = 'certificado/plantilla/plantilla_form.html'
    success_url = reverse_lazy('certificado:plantilla_list')
    titulo = 'Crear Nueva Plantilla'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'name': 'Plantillas', 'url': reverse('certificado:plantilla_list')},
            {'name': 'Crear Plantilla'}
        ]
        
        # Formset de variantes
        if self.request.POST:
            context['variantes_formset'] = VariantePlantillaFormSet(self.request.POST, self.request.FILES)
        else:
            context['variantes_formset'] = VariantePlantillaFormSet()
        
        return context
    
    def form_valid(self, form):
        """
        Validar y guardar plantilla base con sus variantes.
        Usar transacción para asegurar atomicidad.
        """
        context = self.get_context_data()
        variantes_formset = context['variantes_formset']
        
        with transaction.atomic():
            # Validar formset
            if not variantes_formset.is_valid():
                return self.form_invalid(form)
            
            # Guardar plantilla base
            self.object = form.save()
            
            # Guardar variantes
            variantes_formset.instance = self.object
            variantes_formset.save()
            
            # Mensaje de éxito
            num_variantes = len([f for f in variantes_formset if f.cleaned_data and not f.cleaned_data.get('DELETE', False)])
            if num_variantes > 0:
                messages.success(
                    self.request,
                    f'Plantilla "{self.object.nombre}" creada exitosamente con {num_variantes} variante(s).'
                )
            else:
                messages.success(
                    self.request,
                    f'Plantilla "{self.object.nombre}" creada exitosamente.'
                )
        
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)


class PlantillaUpdateView(LoginRequiredMixin, BaseCatalogoMixin, UpdateView):
    """
    Vista para editar plantilla base y sus variantes.
    """
    model = PlantillaBase
    form_class = PlantillaBaseForm
    template_name = 'certificado/plantilla/plantilla_form.html'
    success_url = reverse_lazy('certificado:plantilla_list')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar: {self.object.nombre}'
        context['breadcrumbs'] = [
            {'name': 'Plantillas', 'url': reverse('certificado:plantilla_list')},
            {'name': 'Editar Plantilla'}
        ]
        
        # Formset de variantes
        if self.request.POST:
            context['variantes_formset'] = VariantePlantillaFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object
            )
        else:
            context['variantes_formset'] = VariantePlantillaFormSet(instance=self.object)
        
        return context
    
    def form_valid(self, form):
        """Validar y guardar cambios en plantilla y variantes"""
        context = self.get_context_data()
        variantes_formset = context['variantes_formset']
        
        with transaction.atomic():
            # Validar formset
            if not variantes_formset.is_valid():
                return self.form_invalid(form)
            
            # Guardar plantilla base
            self.object = form.save()
            
            # Guardar variantes
            variantes_formset.instance = self.object
            variantes_formset.save()
            
            messages.success(
                self.request,
                f'Plantilla "{self.object.nombre}" actualizada exitosamente.'
            )
        
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)


class PlantillaDeleteView(LoginRequiredMixin, BaseCatalogoMixin, DeleteView):
    """
    Vista para eliminar plantilla base (y sus variantes en cascada).
    """
    model = PlantillaBase
    template_name = 'certificado/plantilla/plantilla_confirm_delete.html'
    success_url = reverse_lazy('certificado:plantilla_list')
    titulo = 'Eliminar Plantilla'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'name': 'Plantillas', 'url': reverse('certificado:plantilla_list')},
            {'name': 'Eliminar Plantilla'}
        ]
        context['num_variantes'] = self.object.variantes.count()
        return context
    
    def delete(self, request, *args, **kwargs):
        plantilla_nombre = self.get_object().nombre
        response = super().delete(request, *args, **kwargs)
        messages.success(
            self.request,
            f'Plantilla "{plantilla_nombre}" eliminada exitosamente.'
        )
        return response
