from django.contrib import admin
from django.utils.html import format_html
from .models import Curso, Estudiante, PlantillaCertificado, Certificado

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'responsable', 'estado', 'verificar_nas', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion', 'responsable')
    
    def verificar_nas(self, obj):
        status = obj.status_excel
        if status['exists']:
            return format_html('<span style="color: green;">✅ OK</span>')
        return format_html('<span style="color: red;" title="{}">❌ Error</span>', status['error'])
    verificar_nas.short_description = 'NAS Excel'

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'cedula', 'correo', 'curso', 'fecha_registro')
    list_filter = ('curso', 'fecha_registro')
    search_fields = ('nombre_completo', 'cedula', 'correo')
    raw_id_fields = ('curso',)

@admin.register(PlantillaCertificado)
class PlantillaCertificadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'verificar_nas', 'fecha_creacion')
    search_fields = ('nombre',)

    def verificar_nas(self, obj):
        status = obj.status_archivo
        if status['exists']:
            return format_html('<span style="color: green;">✅ OK</span>')
        return format_html('<span style="color: red;" title="{}">❌ Error</span>', status['error'])
    verificar_nas.short_description = 'NAS Archivo'

@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'codigo_verificacion', 'verificar_nas', 'fecha_generacion')
    list_filter = ('fecha_generacion', 'plantilla')
    search_fields = ('estudiante__nombre_completo', 'estudiante__cedula', 'codigo_verificacion')
    raw_id_fields = ('estudiante',)

    def verificar_nas(self, obj):
        status = obj.status_archivo
        if status['exists']:
            return format_html('<span style="color: green;">✅ OK</span>')
        return format_html('<span style="color: red;" title="{}">❌ No listo</span>', status['error'])
    verificar_nas.short_description = 'NAS PDF'
