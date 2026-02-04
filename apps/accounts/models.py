from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modelo de usuario personalizado para el sistema de certificados.
    Permite control granular sobre las acciones del administrador.
    """
    is_only_read = models.BooleanField('Solo Lectura', default=False)
    can_modify = models.BooleanField('Puede Modificar', default=True)
    can_delete = models.BooleanField('Puede Eliminar', default=False)
    can_send_email = models.BooleanField('Puede Enviar Emails', default=False)

    class Meta:
        db_table = 'auth_user' 
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.username
