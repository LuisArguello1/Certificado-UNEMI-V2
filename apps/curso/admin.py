from django.contrib import admin
from .models import Curso, Estudiante, PlantillaCertificado, Certificado

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'responsable', 'fecha_inicio', 'fecha_fin', 'fecha_creacion')
    list_filter = ('fecha_creacion', 'fecha_inicio')
    search_fields = ('nombre', 'descripcion', 'responsable')
    date_hierarchy = 'fecha_creacion'

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'cedula', 'correo', 'curso', 'fecha_registro')
    list_filter = ('curso', 'fecha_registro')
    search_fields = ('nombre_completo', 'cedula', 'correo')
    raw_id_fields = ('curso',)

@admin.register(PlantillaCertificado)
class PlantillaCertificadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    search_fields = ('nombre',)

@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'codigo_verificacion', 'fecha_generacion')
    list_filter = ('fecha_generacion', 'plantilla')
    search_fields = ('estudiante__nombre_completo', 'estudiante__cedula', 'codigo_verificacion')
    raw_id_fields = ('estudiante',)
