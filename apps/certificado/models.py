"""
Modelos para el sistema de generación automática de certificados.

Este módulo define todos los modelos de base de datos necesarios para:
- Gestión de direcciones/gestiones institucionales
- Plantillas base y variantes de certificados
- Eventos y estudiantes
- Tracking de certificados generados
- Estado de procesamiento en lote

Arquitectura:
    Direccion → PlantillaBase → VariantePlantilla
    Evento → Estudiante → Certificado
    ProcesamientoLote (tracking de batch)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.utils import timezone
from datetime import datetime
import uuid
import os
from django.utils import timezone
from datetime import date

# =============================================================================
# PATH GENERATORS
# =============================================================================

def plantilla_base_path(instance, filename):
    """
    Ruta para plantillas base: plantillas_certificado/base/{direccion_codigo}/{año}/tpl_{uuid}.docx
    """
    ext = os.path.splitext(filename)[1].lower()
    year = datetime.now().year
    uid = uuid.uuid4().hex[:12]
    direccion_codigo = instance.direccion.codigo if instance.direccion else 'general'
    return f'plantillas_certificado/base/{direccion_codigo}/{year}/tpl_{uid}{ext}'


def variante_plantilla_path(instance, filename):
    """
    Ruta para variantes: plantillas_certificado/variantes/{direccion_codigo}/{año}/var_{uuid}.docx
    """
    ext = os.path.splitext(filename)[1].lower()
    year = datetime.now().year
    uid = uuid.uuid4().hex[:12]
    direccion_codigo = instance.plantilla_base.direccion.codigo
    return f'plantillas_certificado/variantes/{direccion_codigo}/{year}/var_{uid}{ext}'


def estudiantes_excel_path(instance, filename):
    """
    Ruta para Excel de estudiantes: eventos/{evento_id}/estudiantes.xlsx
    """
    ext = os.path.splitext(filename)[1].lower()
    return f'eventos/{instance.id}/estudiantes{ext}'


def certificado_docx_path(instance, filename):
    """
    Ruta para DOCX generado: certificados/{evento_id}/{estudiante_id}/certificado.docx
    """
    evento_id = instance.evento.id
    estudiante_id = instance.estudiante.id
    return f'certificados/{evento_id}/{estudiante_id}/certificado.docx'


def certificado_pdf_path(instance, filename):
    """
    Ruta para PDF generado: certificados/{evento_id}/{estudiante_id}/certificado.pdf
    """
    evento_id = instance.evento.id
    estudiante_id = instance.estudiante.id
    return f'certificados/{evento_id}/{estudiante_id}/certificado.pdf'

# =============================================================================
# MODELOS
# =============================================================================

class Direccion(models.Model):
    """
    Catálogo de direcciones/gestiones institucionales.
    Cada dirección tendrá sus propias plantillas de certificado.
    
    Ejemplos:
        - Dirección de Vinculación
        - Dirección Académica
        - Gestión de Capacitación
    """
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Dirección/Gestión',
        unique=True
    )
    codigo = models.CharField(
        max_length=20,
        verbose_name='Código',
        unique=True,
        help_text='Código corto para identificación (ej: DV, DAC)'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Solo las direcciones activas aparecen en formularios'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Dirección/Gestión'
        verbose_name_plural = 'Direcciones/Gestiones'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Modalidad(models.Model):
    """
    Catálogo de modalidades para eventos.
    
    Ejemplos:
        - Virtual
        - Presencial
        - Híbrido
    """
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre de la Modalidad',
        unique=True
    )
    codigo = models.CharField(
        max_length=20,
        verbose_name='Código',
        unique=True,
        help_text='Código corto (ej: VIR, PRE, HIB)'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Solo las modalidades activas aparecen en formularios'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Modalidad'
        verbose_name_plural = 'Modalidades'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Tipo(models.Model):
    """
    Catálogo de tipos de eventos.
    
    Ejemplos:
        - Curso
        - Taller
        - Seminario
        - Conferencia
        - Capacitación
        - Diplomado
    """
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del Tipo',
        unique=True
    )
    codigo = models.CharField(
        max_length=20,
        verbose_name='Código',
        unique=True,
        help_text='Código corto (ej: CUR, TAL, SEM)'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Solo los tipos activos aparecen en formularios'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Tipo'
        verbose_name_plural = 'Tipos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class TipoEvento(models.Model):
    """
    Catálogo de tipos específicos de eventos.
    Descripción más detallada del evento.
    
    Ejemplos:
        - "Curso de Capacitación en Gestión Administrativa"
        - "Taller de Liderazgo Empresarial"
        - "Seminario Internacional de Innovación"
    """
    nombre = models.CharField(
        max_length=200,
        verbose_name='Descripción del Tipo de Evento',
        unique=True
    )
    codigo = models.CharField(
        max_length=20,
        verbose_name='Código',
        unique=True,
        help_text='Código corto'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Solo los tipos activos aparecen en formularios'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Tipo de Evento'
        verbose_name_plural = 'Tipos de Evento'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class PlantillaBase(models.Model):
    """
    Plantilla base de certificado en formato Word (.docx).
    Contiene las variables universales que serán reemplazadas.
    
    Regla de negocio: Solo puede haber una plantilla activa por dirección.
    
    Variables universales soportadas:
        {{NOMBRES}}, {{MODALIDAD}}, {{NOMBRE_EVENTO}}, {{DURACION}},
        {{FECHA_INICIO}}, {{FECHA_FIN}}, {{TIPO}}, {{TIPO_EVENTO}},
        {{FECHA_EMISION}}, {{OBJETIVO_PROGRAMA}}, {{CONTENIDO}}
    """
    direccion = models.ForeignKey(
        Direccion,
        on_delete=models.CASCADE,
        related_name='plantillas_base',
        verbose_name='Dirección/Gestión'
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Plantilla'
    )
    archivo = models.FileField(
        upload_to=plantilla_base_path,
        validators=[FileExtensionValidator(allowed_extensions=['docx'])],
        verbose_name='Archivo Word (.docx)',
        help_text='Plantilla con variables {{VARIABLE}}'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    es_activa = models.BooleanField(
        default=True,
        verbose_name='Es Activa',
        help_text='Solo una plantilla activa por dirección'
    )
    variables_disponibles = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Variables Disponibles',
        help_text='Lista de variables encontradas en la plantilla'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Plantilla Base'
        verbose_name_plural = 'Plantillas Base'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['direccion'],
                condition=models.Q(es_activa=True),
                name='unique_active_plantilla_per_direccion'
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.direccion.codigo})"

    def save(self, *args, **kwargs):
        """
        Override save para asegurar solo una plantilla activa por dirección.
        """
        if self.es_activa:
            # Desactivar otras plantillas de la misma dirección
            PlantillaBase.objects.filter(
                direccion=self.direccion,
                es_activa=True
            ).exclude(pk=self.pk).update(es_activa=False)
        super().save(*args, **kwargs)


class VariantePlantilla(models.Model):
    """
    Variantes de una plantilla base.
    Permite tener múltiples versiones de certificado para una misma dirección.
    
    Ejemplos:
        - "Con Logo Grande"
        - "Modalidad Virtual"
        - "Con Marco Dorado"
        - "Versión Bilingüe"
    
    El usuario puede seleccionar la variante al crear el evento,
    o usar la plantilla base si no selecciona ninguna.
    """
    plantilla_base = models.ForeignKey(
        PlantillaBase,
        on_delete=models.CASCADE,
        related_name='variantes',
        verbose_name='Plantilla Base'
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Variante',
        help_text='Ej: Con Logo Grande, Modalidad Virtual'
    )
    archivo = models.FileField(
        upload_to=variante_plantilla_path,
        validators=[FileExtensionValidator(allowed_extensions=['docx'])],
        verbose_name='Archivo Word (.docx)',
        help_text='Variante de la plantilla base'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el selector'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Solo las variantes activas aparecen en formularios'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Variante de Plantilla'
        verbose_name_plural = 'Variantes de Plantillas'
        ordering = ['plantilla_base', 'orden', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.plantilla_base.nombre})"


class Evento(models.Model):
    """
    Evento para el cual se generarán certificados.
    Contiene toda la información del formulario web.
    
    Los datos de este modelo se usan para reemplazar las variables
    universales en las plantillas de certificado.
    """
    
    # Relaciones
    direccion = models.ForeignKey(
        Direccion,
        on_delete=models.PROTECT,
        related_name='eventos',
        verbose_name='Dirección/Gestión'
    )
    plantilla_seleccionada = models.ForeignKey(
        VariantePlantilla,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos',
        verbose_name='Variante de Plantilla Seleccionada',
        help_text='Si no se selecciona, se usa la plantilla base'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Creado por'
    )
    
    # Campos del formulario (actualizados a ForeignKey)
    modalidad = models.ForeignKey(
        Modalidad,
        on_delete=models.PROTECT,
        related_name='eventos',
        verbose_name='Modalidad'
    )
    nombre_evento = models.CharField(
        max_length=300,
        verbose_name='Nombre del Evento'
    )
    duracion_horas = models.CharField(
        max_length=100,
        verbose_name='Duración',
        help_text='Ej: 40 horas, 3 días'
    )
    fecha_inicio = models.DateField(
        verbose_name='Fecha de Inicio'
    )
    fecha_fin = models.DateField(
        verbose_name='Fecha de Fin'
    )
    tipo = models.ForeignKey(
        Tipo,
        on_delete=models.PROTECT,
        related_name='eventos',
        verbose_name='Tipo'
    )
    tipo_evento = models.ForeignKey(
        TipoEvento,
        on_delete=models.PROTECT,
        related_name='eventos',
        verbose_name='Tipo de Evento',
        help_text='Descripción específica del tipo de evento'
    )
    fecha_emision = models.DateField(
        default=timezone.now,
        verbose_name='Fecha de Emisión'
    )
    
    
    # Configuración de Seguridad
    incluir_qr = models.BooleanField(
        default=False,
        verbose_name='Incluir QR de Seguridad',
        help_text='Si se activa, se estampará un código QR único en cada certificado generado.'
    )

    objetivo_programa = models.TextField(
        verbose_name='Objetivo del Programa'
    )
    contenido_programa = models.TextField(
        verbose_name='Contenido del Programa'
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-fecha_inicio', '-created_at']

    def __str__(self):
        return f"{self.nombre_evento} ({self.fecha_inicio.year})"

    def clean(self):
        """
        Validación: fecha_fin >= fecha_inicio
        """
        from django.core.exceptions import ValidationError
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({
                'fecha_fin': 'La fecha de fin debe ser posterior o igual a la fecha de inicio.'
            })


class Estudiante(models.Model):
    """
    Estudiante participante en un evento.
    Los datos provienen del archivo Excel cargado por el usuario.
    
    Formato Excel requerido:
        - Columna 1: NOMBRES COMPLETOS
        - Columna 2: CORREO ELECTRONICO
    """
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='estudiantes',
        verbose_name='Evento'
    )
    nombres_completos = models.CharField(
        max_length=300,
        verbose_name='Nombres Completos'
    )
    correo_electronico = models.EmailField(
        verbose_name='Correo Electrónico'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de registro'
    )

    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['nombres_completos']
        constraints = [
            models.UniqueConstraint(
                fields=['evento', 'correo_electronico'],
                name='unique_estudiante_por_evento'
            )
        ]

    def __str__(self):
        return f"{self.nombres_completos} ({self.evento.nombre_evento})"


class Certificado(models.Model):
    """
    Certificado generado para un estudiante.
    Tracking completo del estado de generación y envío.
    
    Estado del ciclo de vida:
        pending → generating → completed → sending_email → sent
        O: pending → generating → failed
    """
    
    ESTADO_CHOICES = [
        ('pending', 'Pendiente'),
        ('generating', 'Generando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('sending_email', 'Enviando Email'),
        ('sent', 'Enviado'),
    ]

    # Relaciones
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='certificados',
        verbose_name='Evento'
    )
    estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.CASCADE,
        related_name='certificados',
        verbose_name='Estudiante'
    )
    
    # Archivos generados
    archivo_docx = models.FileField(
        upload_to=certificado_docx_path,
        null=True,
        blank=True,
        verbose_name='Archivo DOCX Generado'
    )
    archivo_pdf = models.FileField(
        upload_to=certificado_pdf_path,
        null=True,
        blank=True,
        verbose_name='Archivo PDF Generado'
    )
    
    # Estado y tracking
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pending',
        verbose_name='Estado'
    )

    
    # Campo único para validación pública (QR)
    uuid_validacion = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        null=True,
        blank=True,
        verbose_name='UUID de Validación'
    )
    
    enviado_email = models.BooleanField(
        default=False,
        verbose_name='Email Enviado'
    )
    fecha_envio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Envío'
    )
    intentos_envio = models.PositiveIntegerField(
        default=0,
        verbose_name='Intentos de Envío'
    )
    error_mensaje = models.TextField(
        blank=True,
        verbose_name='Mensaje de Error',
        help_text='Detalles del error si la generación falló'
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['evento', 'estado']),
            models.Index(fields=['estudiante']),
            models.Index(fields=['estado']),
        ]

    def delete(self, *args, **kwargs):
        """
        Elimina el registro y los archivos físicos asociados (PDF/DOCX).
        Override seguro para mantener limpio el almacenamiento.
        """
        # Rutas a eliminar
        paths_to_remove = []
        try:
            if self.archivo_pdf:
                paths_to_remove.append(self.archivo_pdf.path)
            if self.archivo_docx:
                paths_to_remove.append(self.archivo_docx.path)
        except Exception:
            pass # Si falla obtener path (ej: storage S3), ignorar

        # Eliminar registro DB primero (si falla, no borramos archivos)
        super().delete(*args, **kwargs)

        # Eliminar archivos físicos y limpiar directorios
        dirs_to_clean = set()
        for path in paths_to_remove:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    # Añadir directorio padre a la lista de limpieza
                    dirs_to_clean.add(os.path.dirname(path))
            except Exception as e:
                # Log error pero no romper flujo
                pass
        
        # Intentar eliminar directorios vacíos (ej: carpeta del estudiante)
        for dirty_dir in dirs_to_clean:
            try:
                os.rmdir(dirty_dir) # Solo elimina si está vacío
            except OSError:
                pass # No está vacío o error de permisos

    def __str__(self):
        return f"Certificado de {self.estudiante.nombres_completos} - {self.get_estado_display()}"


class ProcesamientoLote(models.Model):
    """
    Tracking del procesamiento en lote de certificados.
    Permite monitorear el progreso de la generación masiva.
    
    Un ProcesamientoLote se crea por cada evento procesado,
    y rastrea el estado de todos los certificados de ese evento.
    """
    
    ESTADO_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('partial', 'Parcialmente Completado'),
    ]
    
    evento = models.OneToOneField(
        Evento,
        on_delete=models.CASCADE,
        related_name='procesamiento_lote',
        verbose_name='Evento'
    )
    
    # Contadores
    total_estudiantes = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de Estudiantes'
    )
    procesados = models.PositiveIntegerField(
        default=0,
        verbose_name='Procesados'
    )
    exitosos = models.PositiveIntegerField(
        default=0,
        verbose_name='Exitosos'
    )
    fallidos = models.PositiveIntegerField(
        default=0,
        verbose_name='Fallidos'
    )
    
    # Estado
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    
    # Tiempos
    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Inicio'
    )
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Fin'
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Procesamiento en Lote'
        verbose_name_plural = 'Procesamientos en Lote'
        ordering = ['-created_at']

    def __str__(self):
        return f"Lote {self.evento.nombre_evento} - {self.get_estado_display()}"

    @property
    def porcentaje_progreso(self):
        """Retorna el porcentaje de progreso (0-100)"""
        if self.total_estudiantes == 0:
            return 0
        return int((self.procesados / self.total_estudiantes) * 100)

    def actualizar_contadores(self):
        """
        Actualiza los contadores basándose en los certificados del evento.
        """
        from django.db.models import Count, Q
        
        stats = self.evento.certificados.aggregate(
            total=Count('id'),
            completados=Count('id', filter=Q(estado__in=['completed', 'sent'])),
            fallidos=Count('id', filter=Q(estado='failed'))
        )
        
        self.procesados = stats['completados'] + stats['fallidos']
        self.exitosos = stats['completados']
        self.fallidos = stats['fallidos']
        
        # Actualizar estado del lote
        if self.procesados == 0:
            self.estado = 'pending'
        elif self.procesados < self.total_estudiantes:
            self.estado = 'processing'
        elif self.fallidos == 0:
            self.estado = 'completed'
            if not self.fecha_fin:
                self.fecha_fin = timezone.now()
        elif self.exitosos == 0:
            self.estado = 'failed'
            if not self.fecha_fin:
                self.fecha_fin = timezone.now()
        else:
            self.estado = 'partial'
            if not self.fecha_fin:
                self.fecha_fin = timezone.now()
        
        self.save()


class EmailDailyLimit(models.Model):
    """
    Modelo para tracking del límite diario de envío de correos.
    Se usa para evitar exceder el límite impuesto por el servidor SMTP.
    """
    date = models.DateField(
        unique=True, 
        default=date.today,
        verbose_name='Fecha'
    )
    count = models.IntegerField(
        default=0, 
        verbose_name='Correos enviados'
    )
    
    class Meta:
        verbose_name = 'Límite diario de correos'
        verbose_name_plural = 'Límites diarios de correos'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date}: {self.count} correos enviados"
    
    @classmethod
    def can_send_email(cls):
        """
        Verifica si aún se puede enviar un correo sin exceder el límite diario.
        
        Returns:
            bool: True si se puede enviar, False si se alcanzó el límite
        """
        from django.conf import settings
        
        today = date.today()
        limit_record, created = cls.objects.get_or_create(date=today)
        
        daily_limit = getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
        
        return limit_record.count < daily_limit
    
    @classmethod
    def increment_count(cls):
        """
        Incrementa el contador de correos enviados hoy.
        """
        today = date.today()
        from django.db.models import F
        
        today = date.today()
        # Usar get_or_create para asegurar existencia
        limit_record, created = cls.objects.get_or_create(date=today)
        
        # Actualización atómica para evitar race conditions
        limit_record.count = F('count') + 1
        limit_record.save(update_fields=['count'])
        
        # Recargar para obtener valor actualizado si se necesita
        limit_record.refresh_from_db()
        return limit_record.count
    
    @classmethod
    def get_remaining_today(cls):
        """
        Obtiene la cantidad de correos que aún se pueden enviar hoy.
        
        Returns:
            int: Cantidad de correos restantes
        """
        from django.conf import settings
        
        today = date.today()
        limit_record, created = cls.objects.get_or_create(date=today)
        
        daily_limit = getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
        remaining = daily_limit - limit_record.count
        
        return max(0, remaining)

    @classmethod
    def puede_enviar_lote(cls, cantidad):
        """
        Verifica si se puede enviar un lote de emails.
        
        Args:
            cantidad: Número de emails a enviar
        
        Returns:
            tuple: (puede_enviar: bool, emails_restantes: int, mensaje: str)
        """
        restantes = cls.get_remaining_today()
        
        daily_limit = cls.get_limit()
        
        if cantidad > restantes:
            mensaje = (
                f"No se puede enviar el lote. Se requieren {cantidad} emails "
                f"pero solo quedan {restantes} disponibles hoy (límite: {daily_limit}/día)."
            )
            return False, restantes, mensaje
        
        return True, restantes, f"Se pueden enviar {cantidad} emails. Restantes: {restantes - cantidad}"

    @classmethod
    def get_limit(cls):
        from django.conf import settings
        return getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
    
    @classmethod
    def get_usage(cls):
        today = date.today()
        limit_record, created = cls.objects.get_or_create(date=today)
        return limit_record.count

