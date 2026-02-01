
from pathlib import Path

import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent

#Variables de entorno
env = environ.Env(
    DEBUG=(bool, False)
)
# Tomar variables de entorno del archivo .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".trycloudflare.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.trycloudflare.com",
]

# Definición de aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_results',
]

# Aplicaciones de terceros
THIRD_PARTY_APPS = [
    'django_extensions',
    'widget_tweaks',
    'tailwind',
    'theme',
]

# Aplicaciones locales
LOCAL_APPS = [
    'apps.accounts',
    'apps.core',
    'apps.certificado',
]

# Apps solo para DEBUG, y no para produccion
if DEBUG:
    THIRD_PARTY_APPS += ['django_browser_reload']


INSTALLED_APPS = INSTALLED_APPS + THIRD_PARTY_APPS + LOCAL_APPS

TAILWIND_APP_NAME = 'theme'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Middleware solo para DEBUG, y no para produccion
if DEBUG:
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =============================================================================
# AUTENTICACIÓN
# =============================================================================

# Backends de autenticación
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', 
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

# URL del sitio para QR
SITE_URL = env('SITE_URL', default='http://localhost:8000')

# Internacionalización
#Idioma: Español, Pais: Ecuador
LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

# Configuración de seguridad para forzar HTTPS y proteger cookies en producción
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)

# Configuración de archivos de estaticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static",]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuración de archivos de medios
USE_NAS_STORAGE = env.bool('USE_NAS_STORAGE', default=False)
MEDIA_ROOT_PATH = env('MEDIA_ROOT_PATH', default=os.path.join(BASE_DIR, 'media'))

if USE_NAS_STORAGE:
    # Usar ruta del NAS explícita
    MEDIA_ROOT = MEDIA_ROOT_PATH
    # Verificación de salud al inicio (solo log)
    if not os.path.exists(MEDIA_ROOT) and not os.access(os.path.dirname(MEDIA_ROOT), os.W_OK):
        print(f"[CRITICAL] USE_NAS_STORAGE=True pero la ruta '{MEDIA_ROOT}' no es accesible. Las cargas de archivos fallarán.")
else:
    # Usar almacenamiento local
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    if not os.path.exists(MEDIA_ROOT):
        os.makedirs(MEDIA_ROOT, exist_ok=True)
    print(f"[INFO] Usando almacenamiento local: {MEDIA_ROOT}")

MEDIA_URL = '/media/'

# Ruta de LibreOffice para generación de PDFs
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"

# =============================================================================
# CONFIGURACIÓN DE CERTIFICADOS
# =============================================================================

# Rutas de almacenamiento para certificados
CERTIFICADO_STORAGE_PATH = os.path.join(MEDIA_ROOT, 'certificados')
CERTIFICADO_TEMPLATES_PATH = os.path.join(MEDIA_ROOT, 'plantillas_certificado')

# Crear directorios si no existen (con manejo de errores para NAS offline)
try:
    os.makedirs(CERTIFICADO_STORAGE_PATH, exist_ok=True)
    os.makedirs(CERTIFICADO_TEMPLATES_PATH, exist_ok=True)
except Exception as e:
    print(f"[ERROR] No se pudieron crear los directorios de certificados: {e}")
    print("[WARNING] El sistema continuará funcionando, pero las operaciones de archivos fallarán hasta que el almacenamiento esté disponible.")

# Configuración de cache para archivos estáticos y media
STATIC_FILE_MAX_AGE = 60 * 60 * 24 * 30  # 30 días en segundos
MEDIA_FILE_MAX_AGE = 60 * 60 * 24 * 7    # 7 días en segundos

#Npm configuracion para Tailwind
# Intentar obtener de variable de entorno, sino buscar en PATH, sino default 'npm'
import shutil
NPM_BIN_PATH = env('NPM_BIN_PATH', default=shutil.which('npm') or 'npm')

# =============================================================================
# LOGGING
# =============================================================================

LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
        'require_debug_true': {'()': 'django.utils.log.RequireDebugTrue'},
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_error'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps.accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.certificado': {
            'handlers': ['console', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'fontTools': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'PIL': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

#Configuración de envío de correos
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# =============================================================================
# CONFIGURACIÓN DE CELERY
# =============================================================================

# URL de conexión a Redis
CELERY_BROKER_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = 'django-db'  # Guardar resultados en BD Django

# Configuración adicional de Celery
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
# 30 minutos máximo por tarea
CELERY_TASK_TIME_LIMIT = 30 * 60  

# =============================================================================
# CONFIGURACIÓN DE LÍMITES DE ENVÍO DE CORREOS
# =============================================================================

# Límite diario global de correos (para evitar bloqueos del servidor SMTP)
EMAIL_DAILY_LIMIT = env.int('EMAIL_DAILY_LIMIT', default=400)

# Tiempo de espera entre envíos de correos individuales (en segundos)
EMAIL_RATE_LIMIT_SECONDS = env.int('EMAIL_RATE_LIMIT_SECONDS', default=2)

# Cantidad de correos por lote en procesamiento masivo
EMAIL_BATCH_SIZE = env.int('EMAIL_BATCH_SIZE', default=10)


# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD PARA PRODUCCIÓN
# =============================================================================

if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookies seguras
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    
    # HSTS
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Headers de seguridad
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'