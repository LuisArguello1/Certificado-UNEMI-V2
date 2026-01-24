from django.db import models
from django.core.validators import FileExtensionValidator
import os

class PlantillaCertificado(models.Model):
    """
    Modelo para gestionar las plantillas de certificados (fondos).
    """
    nombre = models.CharField(max_length=200, verbose_name='Nombre de la plantilla')
    archivo = models.FileField(
        upload_to='plantillas_certificados/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg'])],
        verbose_name='Archivo de plantilla'
    )
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        verbose_name = 'Plantilla de Certificado'
        verbose_name_plural = 'Plantillas de Certificados'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

class Curso(models.Model):
    """
    Modelo para gestionar los cursos.
    """
    nombre = models.CharField(max_length=200, verbose_name='Nombre del curso')
    descripcion = models.TextField(verbose_name='Descripción', blank= True, null= True)
    responsable = models.CharField(max_length=200, verbose_name='Responsable del curso', blank=False, null=False)
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio', blank=True, null=True)
    fecha_fin = models.DateField(verbose_name='Fecha de fin', blank=True, null=True)
    
    archivo_estudiantes = models.FileField(
        upload_to='cursos/estudiantes/',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        verbose_name='Archivo de Estudiantes (Excel)',
        help_text='Subir archivo con columnas: Nombres, Cedula, Correo'
    )
    plantilla_certificado = models.ForeignKey(
        PlantillaCertificado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Plantilla de Certificado por defecto'
    )
    texto_certificado = models.TextField(
        null=True, 
        blank=True, 
        verbose_name='Texto del Certificado',
        help_text='Contenido del certificado. Use {NOMBRE_ESTUDIANTE}, {CEDULA}, {CURSO}, {FECHA_INICIO}, {FECHA_FIN}, {RESPONSABLE} como variables.'
    )
    configuracion_certificado = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name='Configuración del Certificado',
        help_text='Almacena posiciones, fuentes y texto dinámico.'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

class Estudiante(models.Model):
    """
    Modelo para gestionar los estudiantes inscritos en un curso.
    """
    curso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE, 
        related_name='estudiantes',
        verbose_name='Curso'
    )
    nombre_completo = models.CharField(max_length=300, verbose_name='Nombres y Apellidos completos')
    cedula = models.CharField(max_length=20, verbose_name='Cédula', db_index=True)
    correo = models.EmailField(verbose_name='Correo electrónico')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')

    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['nombre_completo']
        constraints = [
            models.UniqueConstraint(fields=['curso', 'cedula'], name='unique_estudiante_curso')
        ]
        indexes = [
            models.Index(fields=['curso', 'cedula']),
            models.Index(fields=['cedula']),
        ]

    def __str__(self):
        return f"{self.nombre_completo} - {self.cedula}"

class Certificado(models.Model):
    """
    Modelo para los certificados generados.
    """
    estudiante = models.ForeignKey(
        Estudiante, 
        on_delete=models.CASCADE, 
        related_name='certificados',
        verbose_name='Estudiante'
    )
    plantilla = models.ForeignKey(
        PlantillaCertificado,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Plantilla utilizada'
    )
    archivo_generado = models.FileField(
        upload_to='certificados_generados/',
        null=True,
        blank=True,
        verbose_name='Certificado Generado'
    )
    codigo_verificacion = models.CharField(
        max_length=50, 
        unique=True, 
        null=True, 
        blank=True, 
        verbose_name='Código de Verificación'
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de generación')

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"Certificado de {self.estudiante.nombre_completo}"
