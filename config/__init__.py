"""
Inicialización del paquete config.
Importa la aplicación Celery para que se cargue cuando Django inicie.
"""
from __future__ import absolute_import, unicode_literals

# Esto asegura que la app de Celery siempre se importe cuando Django inicia
from .celery import app as celery_app

__all__ = ('celery_app',)
