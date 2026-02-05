# Sistema de Gestión de Certificados UNEMI v2.0

Sistema profesional de generación masiva, firma digital mediante códigos QR y distribución automatizada de certificados académicos en formato PDF.

---

## 📋 Características Principales

- **Generación Masiva**: Procesamiento por lotes con optimización de recursos (LibreOffice en modo headless)
- **Personalización Dinámica**: Sistema de plantillas Word con variables de reemplazo automático
- **Validación QR**: Códigos únicos incrustados para verificación pública de autenticidad
- **Envío Automático**: Distribución inteligente por correo con límites configurables anti-spam
- **Procesamiento Asíncrono**: Celery + Redis para operaciones en segundo plano
- **Seguridad Avanzada**: Content Security Policy (CSP), protección contra fuerza bruta con Django Axes

---

## 🔧 Requisitos del Sistema

### Software Base
- **Python**: 3.10 o superior
- **Base de Datos**: SQLite (incluida) o PostgreSQL (producción)
- **Navegador**: Chrome, Firefox o Edge (última versión)

### Dependencias Externas

#### 1. Redis (Motor de Colas)
Gestiona las tareas asíncronas de generación y envío.

**Windows:**
- Descargar [Redis-x64-3.0.504.msi](https://github.com/microsoftarchive/redis/releases)
- O usar WSL: `sudo apt install redis-server`

**Linux/Mac:**
```bash
sudo apt install redis-server  # Debian/Ubuntu
brew install redis              # macOS
```

#### 2. LibreOffice (Conversor DOCX → PDF)
Convierte documentos Word a PDF manteniendo formato y tipografía.

- Descargar desde [libreoffice.org](https://www.libreoffice.org/download/download/)
- **Windows**: Se instalará en `C:\Program Files\LibreOffice\program\soffice.exe`
- **Linux**: Generalmente en `/usr/bin/soffice`

#### 3. Fuente Poppins (Opcional)
Para diseños visuales consistentes con la identidad institucional.

- Descargar desde [Google Fonts - Poppins](https://fonts.google.com/specimen/Poppins)
- Instalar todas las variantes (Regular, Bold, Black, etc.)

---

## 🚀 Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/LuisArguello1/Certificado-UNEMI-V2.git
cd Certificado-UNEMI-V2
```

### 2. Crear y Activar Entorno Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias Python
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Copie el archivo de ejemplo y modifique según su configuración:
```bash
cp .env.example .env
```

Edite el archivo `.env` con sus credenciales (ver sección siguiente).

### 5. Migrar Base de Datos
```bash
python manage.py migrate
```

### 6. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 7. Verificar Instalación de LibreOffice
El sistema verificará automáticamente la ruta de LibreOffice al iniciar. Si no se encuentra, actualice la variable `LIBREOFFICE_PATH` en su `.env`.

---

## ⚙️ Configuración del Archivo `.env`

Edite el archivo `.env` en la raíz del proyecto:

```ini
# ═══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN GENERAL
# ═══════════════════════════════════════════════════════════════

# Modo de depuración (True para desarrollo, False para producción)
DEBUG=True

# Clave secreta de Django (Generar una única para producción)
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=django-insecure-cambiar-esta-clave-en-produccion

# Ruta personalizada del panel de administración
ADMIN_URL=administration-admin-unemi/

# ═══════════════════════════════════════════════════════════════
#  SEGURIDAD (Producción)
# ═══════════════════════════════════════════════════════════════

# Activar redirección HTTPS (True en producción con SSL)
SECURE_SSL_REDIRECT=False

# Cookies seguras (True en producción)
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Protección contra Fuerza Bruta (Django Axes)
AXES_FAILURE_LIMIT=5
AXES_COOLOFF_MINUTES=15

# Configuración de Sesiones
SESSION_COOKIE_AGE=7200
SESSION_EXPIRE_AT_BROWSER_CLOSE=True

# ═══════════════════════════════════════════════════════════════
#  SMTP - ENVÍO DE CORREOS
# ═══════════════════════════════════════════════════════════════

# Configuración del servidor SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Credenciales del remitente
# IMPORTANTE: Para Gmail, usar "Contraseña de Aplicación"
# Generar en: https://myaccount.google.com/apppasswords
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_clave_de_aplicacion_aqui
DEFAULT_FROM_EMAIL=tu_correo@gmail.com

# Límites de envío (Prevención anti-spam)
EMAIL_DAILY_LIMIT=1800
EMAIL_RATE_LIMIT_SECONDS=2
EMAIL_BATCH_SIZE=10

# ═══════════════════════════════════════════════════════════════
#  REDIS Y CELERY
# ═══════════════════════════════════════════════════════════════

# URL de conexión a Redis (Broker de mensajería)
REDIS_URL=redis://localhost:6379/0

# ═══════════════════════════════════════════════════════════════
#  URL PÚBLICA (Para Códigos QR)
# ═══════════════════════════════════════════════════════════════

# URL base del sistema (usada para generar enlaces de validación QR)
# En desarrollo: http://localhost:8000
# En producción: https://tu-dominio.com
# Con túnel Cloudflare: https://tu-tunel.trycloudflare.com
SITE_URL=http://localhost:8000

# ═══════════════════════════════════════════════════════════════
#  HERRAMIENTAS DEL SISTEMA
# ═══════════════════════════════════════════════════════════════

# Ruta al ejecutable de LibreOffice
# Windows: C:\\Program Files\\LibreOffice\\program\\soffice.exe
# Linux: /usr/bin/soffice
LIBREOFFICE_PATH=C:\\Program Files\\LibreOffice\\program\\soffice.exe
```

---

## ▶️ Ejecución del Sistema

El sistema requiere **3 procesos simultáneos**. Abra 3 ventanas de terminal/consola:

### Terminal 1: Redis Server
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Iniciar Redis (use el script automático)
start_redis.bat  # Windows
redis-server     # Linux/Mac
```

### Terminal 2: Celery Worker
Procesa la cola de generación de certificados:
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Iniciar Celery
start_celery.bat  # Windows
celery -A config worker --loglevel=info  # Linux/Mac
```

### Terminal 3: Servidor Web Django
Interfaz de usuario y API:
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Iniciar servidor de desarrollo
python manage.py runserver
```

**Acceder al sistema:** http://127.0.0.1:8000

---
