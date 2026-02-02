"""
Admin interface para el sistema de certificados.

Registra todos los modelos con interfaces mejoradas y acciones personalizadas.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count
from .models import (
    Direccion,
    PlantillaBase,
    VariantePlantilla,
    Evento,
    Estudiante,
    Certificado,
    ProcesamientoLote,
    Modalidad,
    Tipo,
    TipoEvento
)


@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    """
    Admin para Direcciones/Gestiones.
    """
    list_display = ['codigo', 'nombre', 'activo', 'num_plantillas', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['codigo', 'nombre', 'descripcion']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['codigo']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def num_plantillas(self, obj):
        """Número de plantillas base asociadas"""
        return obj.plantillas_base.count()
    num_plantillas.short_description = 'Plantillas'


@admin.register(Modalidad)
class ModalidadAdmin(admin.ModelAdmin):
    """Admin para el catálogo de Modalidades."""
    list_display = ['codigo', 'nombre', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['nombre']


@admin.register(Tipo)
class TipoAdmin(admin.ModelAdmin):
    """Admin para el catálogo de Tipos (Generales)."""
    list_display = ['codigo', 'nombre', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['nombre']


@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    """Admin para el catálogo de Tipos de Evento (Específicos)."""
    list_display = ['codigo', 'nombre', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['nombre']


@admin.register(PlantillaBase)
class PlantillaBaseAdmin(admin.ModelAdmin):
    """
    Admin para Plantillas Base.
    """
    list_display = ['nombre', 'direccion', 'es_activa', 'num_variantes', 'created_at']
    list_filter = ['direccion', 'es_activa', 'created_at']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['created_at', 'updated_at', 'preview_link']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('direccion', 'nombre', 'descripcion')
        }),
        ('Archivo', {
            'fields': ('archivo', 'preview_link')
        }),
        ('Configuración', {
            'fields': ('es_activa', 'variables_disponibles')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activar_plantilla', 'desactivar_plantilla']
    
    def num_variantes(self, obj):
        """Número de variantes"""
        return obj.variantes.count()
    num_variantes.short_description = 'Variantes'
    
    def preview_link(self, obj):
        """Link para descargar/previsualizar plantilla"""
        if obj.archivo:
            return format_html(
                '<a href="{}" target="_blank">Descargar Plantilla</a>',
                obj.archivo.url
            )
        return '-'
    preview_link.short_description = 'Previsualización'
    
    def activar_plantilla(self, request, queryset):
        """Activar plantillas seleccionadas"""
        for plantilla in queryset:
            plantilla.es_activa = True
            plantilla.save()
        self.message_user(request, f'{queryset.count()} plantilla(s) activada(s).')
    activar_plantilla.short_description = 'Activar plantillas seleccionadas'
    
    def desactivar_plantilla(self, request, queryset):
        """Desactivar plantillas seleccionadas"""
        queryset.update(es_activa=False)
        self.message_user(request, f'{queryset.count()} plantilla(s) desactivada(s).')
    desactivar_plantilla.short_description = 'Desactivar plantillas seleccionadas'


@admin.register(VariantePlantilla)
class VariantePlantillaAdmin(admin.ModelAdmin):
    """
    Admin para Variantes de Plantilla.
    """
    list_display = ['nombre', 'get_direccion', 'plantilla_base', 'activo', 'orden', 'created_at']
    list_filter = ['plantilla_base__direccion', 'plantilla_base', 'activo', 'created_at']
    search_fields = ['nombre', 'descripcion', 'plantilla_base__nombre']
    list_editable = ['orden', 'activo']
    readonly_fields = ['created_at', 'updated_at', 'preview_link']
    ordering = ['plantilla_base', 'orden', 'nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('plantilla_base', 'nombre', 'descripcion')
        }),
        ('Archivo', {
            'fields': ('archivo', 'preview_link')
        }),
        ('Configuración', {
            'fields': ('orden', 'activo')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_direccion(self, obj):
        """Obtener dirección de la plantilla base"""
        return obj.plantilla_base.direccion
    get_direccion.short_description = 'Dirección'
    
    def preview_link(self, obj):
        """Link para descargar/previsualizar variante"""
        if obj.archivo:
            return format_html(
                '<a href="{}" target="_blank">Descargar Variante</a>',
                obj.archivo.url
            )
        return '-'
    preview_link.short_description = 'Previsualización'


class EstudianteInline(admin.TabularInline):
    """
    Inline para mostrar estudiantes en el admin de Evento.
    """
    model = Estudiante
    extra = 0
    readonly_fields = ['nombres_completos', 'correo_electronico', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """
    Admin para Eventos.
    """
    list_display = ['nombre_evento', 'direccion', 'modalidad', 'tipo', 'fecha_inicio', 'num_estudiantes', 'created_by']
    list_filter = ['direccion', 'modalidad', 'tipo', 'fecha_inicio', 'created_at']
    search_fields = ['nombre_evento', 'tipo_evento', 'objetivo_programa']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    date_hierarchy = 'fecha_inicio'
    ordering = ['-fecha_inicio', '-created_at']
    
    fieldsets = (
        ('Configuración', {
            'fields': ('direccion', 'plantilla_seleccionada')
        }),
        ('Información del Evento', {
            'fields': ('nombre_evento', 'modalidad', 'tipo', 'tipo_evento')
        }),
        ('Fechas y Duración', {
            'fields': ('fecha_inicio', 'fecha_fin', 'duracion_horas', 'fecha_emision')
        }),
        ('Contenido', {
            'fields': ('objetivo_programa', 'contenido_programa')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [EstudianteInline]
    
    def num_estudiantes(self, obj):
        """Número de estudiantes en el evento"""
        return obj.estudiantes.count()
    num_estudiantes.short_description = 'Estudiantes'
    
    def save_model(self, request, obj, form, change):
        """Asignar usuario creador si es nuevo"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    """
    Admin para Estudiantes.
    """
    list_display = ['nombres_completos', 'correo_electronico', 'evento', 'num_certificados', 'created_at']
    list_filter = ['evento__direccion', 'evento', 'created_at']
    search_fields = ['nombres_completos', 'correo_electronico', 'evento__nombre_evento']
    readonly_fields = ['created_at']
    ordering = ['nombres_completos']
    
    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('nombres_completos', 'correo_electronico')
        }),
        ('Evento', {
            'fields': ('evento',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def num_certificados(self, obj):
        """Número de certificados generados"""
        return obj.certificados.count()
    num_certificados.short_description = 'Certificados'


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    """
    Admin para Certificados.
    """
    list_display = [
        'get_estudiante', 
        'get_evento', 
        'estado_badge', 
        'enviado_email', 
        'intentos_envio',
        'download_links',
        'created_at'
    ]
    list_filter = [
        'estado', 
        'enviado_email', 
        'estudiante__evento__direccion', 
        'estudiante__evento',
        'created_at'
    ]
    search_fields = [
        'estudiante__nombres_completos', 
        'estudiante__correo_electronico',
        'estudiante__evento__nombre_evento'
    ]
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'download_links',
        'error_mensaje_display'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Relaciones', {
            'fields': ('estudiante',)
        }),
        ('Archivos Generados', {
            'fields': ('archivo_docx', 'archivo_pdf', 'download_links')
        }),
        ('Estado', {
            'fields': ('estado', 'enviado_email', 'fecha_envio', 'intentos_envio')
        }),
        ('Errores', {
            'fields': ('error_mensaje_display',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reintentar_generacion', 'reintentar_envio_email', 'descargar_pdfs']
    
    def get_estudiante(self, obj):
        """Nombre del estudiante"""
        return obj.estudiante.nombres_completos
    get_estudiante.short_description = 'Estudiante'
    
    def get_evento(self, obj):
        """Nombre del evento"""
        return obj.evento.nombre_evento
    get_evento.short_description = 'Evento'
    
    def estado_badge(self, obj):
        """Badge de estado con colores"""
        colors = {
            'pending': '#999',
            'generating': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545',
            'sending_email': '#ffc107',
            'sent': '#17a2b8',
        }
        color = colors.get(obj.estado, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def download_links(self, obj):
        """Links de descarga para archivos"""
        links = []
        if obj.archivo_docx:
            links.append(format_html(
                '<a href="{}" target="_blank" style="margin-right: 10px;">📄 DOCX</a>',
                obj.archivo_docx.url
            ))
        if obj.archivo_pdf:
            links.append(format_html(
                '<a href="{}" target="_blank">📕 PDF</a>',
                obj.archivo_pdf.url
            ))
        return mark_safe(' '.join(links)) if links else '-'
    download_links.short_description = 'Descargar'
    
    def error_mensaje_display(self, obj):
        """Mostrar mensaje de error formateado"""
        if obj.error_mensaje:
            return format_html('<pre style="background: #f5f5f5; padding: 10px;">{}</pre>', obj.error_mensaje)
        return '-'
    error_mensaje_display.short_description = 'Mensaje de Error'
    
    def reintentar_generacion(self, request, queryset):
        """Reintentar generación de certificados fallidos"""
        from .tasks import generate_and_send_certificate_task
        
        fallidos = queryset.filter(estado='failed')
        count = 0
        
        for certificado in fallidos:
            certificado.estado = 'pending'
            certificado.error_mensaje = ''
            certificado.save()
            
            # Re-encolar tarea Celery
            generate_and_send_certificate_task.delay(certificado.id)
            count += 1
        
        self.message_user(request, f'{count} certificado(s) re-encolado(s) para generación.')
    reintentar_generacion.short_description = 'Reintentar generación (solo fallidos)'
    
    def reintentar_envio_email(self, request, queryset):
        """Reintentar envío de email para certificados completados pero no enviados"""
        from .tasks import send_certificate_email_task
        
        pendientes = queryset.filter(
            estado__in=['completed', 'failed'],
            enviado_email=False
        ).exclude(archivo_pdf='')
        
        count = 0
        for certificado in pendientes:
            certificado.estado = 'completed'
            certificado.save()
            
            # Encolar tarea de envío
            send_certificate_email_task.delay(certificado.id)
            count += 1
        
        self.message_user(request, f'{count} email(s) re-encolado(s) para envío.')
    reintentar_envio_email.short_description = 'Reintentar envío de email'
    
    def descargar_pdfs(self, request, queryset):
        """Preparar descarga masiva de PDFs"""
        # TODO: Implementar generación de ZIP con todos los PDFs
        self.message_user(request, 'Función de descarga masiva en desarrollo.')
    descargar_pdfs.short_description = 'Descargar PDFs seleccionados (ZIP)'


@admin.register(ProcesamientoLote)
class ProcesamientoLoteAdmin(admin.ModelAdmin):
    """
    Admin para Procesamiento en Lote.
    """
    list_display = [
        'get_evento_nombre',
        'estado_badge',
        'progreso_display',
        'contadores_display',
        'fecha_inicio',
        'duracion'
    ]
    list_filter = ['estado', 'created_at']
    search_fields = ['evento__nombre_evento']
    readonly_fields = [
        'evento',
        'total_estudiantes',
        'procesados',
        'exitosos',
        'fallidos',
        'fecha_inicio',
        'fecha_fin',
        'created_at',
        'updated_at',
        'progreso_bar'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Evento', {
            'fields': ('evento',)
        }),
        ('Progreso', {
            'fields': ('estado', 'progreso_bar')
        }),
        ('Contadores', {
            'fields': ('total_estudiantes', 'procesados', 'exitosos', 'fallidos')
        }),
        ('Tiempos', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_evento_nombre(self, obj):
        """Nombre del evento"""
        return obj.evento.nombre_evento
    get_evento_nombre.short_description = 'Evento'
    
    def estado_badge(self, obj):
        """Badge de estado con colores"""
        colors = {
            'pending': '#999',
            'processing': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545',
            'partial': '#ffc107',
        }
        color = colors.get(obj.estado, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def progreso_display(self, obj):
        """Mostrar porcentaje de progreso"""
        return f"{obj.porcentaje_progreso}%"
    progreso_display.short_description = 'Progreso'
    
    def contadores_display(self, obj):
        """Mostrar contadores resumidos"""
        return format_html(
            '<span style="color: green;">✓ {}</span> / '
            '<span style="color: red;">✗ {}</span> / '
            '<span style="color: gray;">⏳ {}</span>',
            obj.exitosos,
            obj.fallidos,
            obj.total_estudiantes - obj.procesados
        )
    contadores_display.short_description = 'Exitosos / Fallidos / Pendientes'
    
    def progreso_bar(self, obj):
        """Barra de progreso visual"""
        porcentaje = obj.porcentaje_progreso
        return format_html(
            '<div style="width: 100%; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: #28a745; color: white; text-align: center; padding: 5px; border-radius: 3px;">'
            '{}%'
            '</div>'
            '</div>',
            porcentaje,
            porcentaje
        )
    progreso_bar.short_description = 'Barra de Progreso'
    
    def duracion(self, obj):
        """Duración del procesamiento"""
        if obj.fecha_inicio and obj.fecha_fin:
            delta = obj.fecha_fin - obj.fecha_inicio
            segundos = int(delta.total_seconds())
            minutos = segundos // 60
            segundos_restantes = segundos % 60
            return f"{minutos}m {segundos_restantes}s"
        elif obj.fecha_inicio:
            return "En proceso..."
        return "-"
    duracion.short_description = 'Duración'
    
    def has_add_permission(self, request):
        """No permitir creación manual de lotes"""
        return False
