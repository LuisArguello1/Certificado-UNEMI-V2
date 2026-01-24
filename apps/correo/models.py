"""
Modelos para la app Correo.

Gestiona campañas de correo masivo y destinatarios, vinculándolos a los Cursos.
"""
from django.db import models
from apps.curso.models import Curso

class EmailCampaign(models.Model):
    """
    Modelo para almacenar campañas de correo masivo.
    Ahora vinculadas directamente a un Curso.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    course = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE, 
        related_name='campaigns',
        verbose_name='Curso Asociado',
        null=True, # Allow null temporarily to avoid migration issues if existing data
        blank=False
    )
    
    name = models.CharField(max_length=200, verbose_name='Nombre de la campaña')
    subject = models.CharField(max_length=300, verbose_name='Asunto del correo')
    # message almacenará HTML del editor de texto enriquecido
    message = models.TextField(blank=True, verbose_name='Mensaje personalizado (HTML)')
    
    # Deprecated: excel_file. The source is now the course.
    # We keep it locally just in case we need to migrate/reference old logic, 
    # but for new logic we rely on 'course'.
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft', 
        verbose_name='Estado'
    )
    
    total_recipients = models.IntegerField(default=0, verbose_name='Total de destinatarios')
    sent_count = models.IntegerField(default=0, verbose_name='Correos enviados')
    failed_count = models.IntegerField(default=0, verbose_name='Correos fallidos')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de envío')
    
    class Meta:
        verbose_name = 'Campaña de correo'
        verbose_name_plural = 'Campañas de correo'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.course.nombre if self.course else 'Sin curso'}"
    
    def update_statistics(self):
        """Actualiza las estadísticas de la campaña."""
        self.sent_count = self.recipients.filter(status='sent').count()
        self.failed_count = self.recipients.filter(status='failed').count()
        self.save()


class EmailRecipient(models.Model):
    """
    Modelo para almacenar destinatarios individuales de una campaña.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
    ]
    
    campaign = models.ForeignKey(
        EmailCampaign, 
        on_delete=models.CASCADE, 
        related_name='recipients',
        verbose_name='Campaña'
    )
    # Copiamos datos del estudiante para tener histórico inmutable
    full_name = models.CharField(max_length=300, verbose_name='Nombre completo')
    email = models.EmailField(verbose_name='Correo electrónico')
    
    # Link al portal donde el estudiante pone su cédula
    certificate_link = models.URLField(max_length=500, verbose_name='Link del portal')
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending', 
        verbose_name='Estado'
    )
    error_message = models.TextField(blank=True, verbose_name='Mensaje de error')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de envío')
    
    class Meta:
        verbose_name = 'Destinatario'
        verbose_name_plural = 'Destinatarios'
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} - {self.email}"
