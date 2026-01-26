from django.db import models
from django.core.validators import FileExtensionValidator
from datetime import datetime
import uuid
import hashlib
import os

# =============================================================================
# UTILIDADES DE STORAGE
# =============================================================================

def hash_name(seed: str):
    """
    Genera un hash SHA-256 corto para anonimizar nombres de archivos.
    """
    raw = f"{seed}-{uuid.uuid4()}".encode()
    return hashlib.sha256(raw).hexdigest()[:32]

# =============================================================================
# PATH GENERATORS
# =============================================================================

def plantilla_path(instance, filename):
    """
    Ruta: plantillas/<año>/tpl_<uuid><ext>
    """
    ext = os.path.splitext(filename)[1].lower()
    year = datetime.now().year
    uid = uuid.uuid4().hex
    return f'plantillas/{year}/tpl_{uid}{ext}'

def estudiantes_excel_path(instance, filename):
    """
    Ruta: cursos/<curso_id>/estudiantes<ext>
    """
    ext = os.path.splitext(filename)[1].lower()
    return f'cursos/{instance.id}/estudiantes{ext}'

def certificado_path(instance, filename):
    """
    Ruta: certificados/<curso_id>/<estudiante_id>/<año>/cert_<hash><ext>
    """
    ext = os.path.splitext(filename)[1].lower()
    year = datetime.now().year
    curso_id = instance.estudiante.curso.id
    estudiante_id = instance.estudiante.id
    h = hash_name(f"{curso_id}-{estudiante_id}")
    return f'certificados/{curso_id}/{estudiante_id}/{year}/cert_{h}{ext}'

# Alias para mantener compatibilidad con migraciones antiguas
certificate_directory_path = certificado_path

class PlantillaCertificado(models.Model):
    """
    Modelo para gestionar las plantillas de certificados (fondos).
    """
    nombre = models.CharField(max_length=200, verbose_name='Nombre de la plantilla')
    archivo = models.FileField(
        upload_to=plantilla_path,
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

    @property
    def status_archivo(self):
        """
        Retorna el estado real del archivo en el NAS.
        """
        from apps.core.services.storage_service import StorageService
        return StorageService.get_file_status(self.archivo)

class Curso(models.Model):
    """
    Modelo para gestionar los cursos.
    """
    # Unique=True for course name to safely use it as folder name
    nombre = models.CharField(max_length=200, verbose_name='Nombre del curso', unique=True, db_index=True)
    descripcion = models.TextField(verbose_name='Descripción', blank= True, null= True)
    responsable = models.CharField(max_length=200, verbose_name='Responsable del curso', blank=False, null=False)
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio', blank=True, null=True)
    fecha_fin = models.DateField(verbose_name='Fecha de fin', blank=True, null=True)
    
    archivo_estudiantes = models.FileField(
        upload_to=estudiantes_excel_path,
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

    @property
    def configuracion_certificado_json(self):
        import json
        if self.configuracion_certificado:
            return json.dumps(self.configuracion_certificado)
        return "{}"
    
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('oculto', 'Oculto'),
        ('archivado', 'Archivado'),
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='disponible',
        verbose_name='Estado',
        help_text='Estado del curso en el portal público'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

    @property
    def status_excel(self):
        """
        Retorna el estado real del archivo Excel en el NAS.
        """
        from apps.core.services.storage_service import StorageService
        return StorageService.get_file_status(self.archivo_estudiantes)

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

def generate_verification_code():
    return uuid.uuid4().hex[:12].upper()

class Certificado(models.Model):
    """
    Certificados generados por estudiante
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
        upload_to=certificado_path,
        null=True,
        blank=True,
        verbose_name='Certificado Generado'
    )
    codigo_verificacion = models.CharField(
        max_length=50,
        unique=True,
        default=generate_verification_code,
        verbose_name='Código de Verificación',
        db_index=True
    )

    # Seguridad y auditoría
    is_public = models.BooleanField(default=False, verbose_name='Acceso público')
    access_count = models.PositiveIntegerField(default=0, verbose_name='Número de accesos')
    last_access = models.DateTimeField(null=True, blank=True, verbose_name='Último acceso')
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de generación')

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'
        ordering = ['-fecha_generacion']
        indexes = [
            models.Index(fields=['codigo_verificacion']),
            models.Index(fields=['estudiante']),
            models.Index(fields=['plantilla']),
        ]

    def __str__(self):
        return f"Certificado de {self.estudiante.nombre_completo}"

    @property
    def status_archivo(self):
        """
        Retorna el estado real del archivo en el NAS.
        """
        from apps.core.services.storage_service import StorageService
        return StorageService.get_file_status(self.archivo_generado)

