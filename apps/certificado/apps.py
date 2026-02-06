from django.apps import AppConfig


class CertificadoConfig(AppConfig):
    name = 'apps.certificado'

    def ready(self):
        import apps.certificado.signals
