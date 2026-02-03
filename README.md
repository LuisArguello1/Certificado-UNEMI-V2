# Sistema de Gestión de Certificados UNEMI v2.0

Sistema profesional de generación masiva, firma digital mediante códigos QR y distribución automatizada de certificados académicos en formato PDF.

---

## Características Principales

- **Generación Masiva**: Procesamiento por lotes con optimización de recursos (LibreOffice en modo headless).
- **Personalización Dinámica**: Sistema de plantillas Word con variables de reemplazo automático.
- **Validación QR**: Códigos únicos incrustados para verificación pública de autenticidad.
- **Envío Automático**: Distribución inteligente por correo con límites configurables anti-spam.
- **Procesamiento Asíncrono**: Celery + Redis para operaciones en segundo plano.
---

## Requisitos del Sistema

### Software Base
- **Python**: 3.10 o superior
- **Navegador**: Chrome, Firefox o Edge (versión reciente)

### Dependencias Externas

#### 1. Redis (Motor de Colas)
Gestiona las tareas asíncronas de generación y envío.

- **Windows**: Descargar [Redis-x64-3.0.504.msi](https://github.com/microsoftarchive/redis/releases)
- **Linux**: `sudo apt install redis-server`

#### 2. LibreOffice (Conversor DOCX → PDF)
Convierte documentos Word a PDF manteniendo formato y tipografía.

- Descargar desde [libreoffice.org](https://www.libreoffice.org/download/download/)
- En Windows se instalará en: `C:\Program Files\LibreOffice\program\soffice.exe`

#### 3. Fuente Poppins (Opcional pero Recomendado)
Para diseños visuales consistentes con la identidad institucional.

- Descargar desde [Google Fonts - Poppins](https://fonts.google.com/specimen/Poppins)
- Instalar todas las variantes de peso (Regular, Bold, Black, etc.)

---

## Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/LuisArguello1/Certificado-UNEMI-V2.git
cd Certificado-UNEMI-V2
```

### 2. Crear y Activar Entorno Virtual
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Instalar Dependencias Python
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Cree un archivo `.env` en la raíz del proyecto (copie el ejemplo de abajo y modifique según su configuración).

### 5. Migrar Base de Datos
```bash
python manage.py migrate
```

### 6. Crear Superusuario
```bash
python manage.py createsuperuser
```

---

## Configuración del Archivo `.env`

Cree un archivo llamado `.env` en la raíz del proyecto con el siguiente contenido:

```ini
# ═══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN GENERAL
# ═══════════════════════════════════════════════════════════════

# Modo de depuración (True para desarrollo, False para producción)
DEBUG=True

# Clave secreta de Django (Generar una única para producción con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
SECRET_KEY=django-insecure-cambiar-esta-clave-en-produccion


# ═══════════════════════════════════════════════════════════════
#  SEGURIDAD (Producción)
# ═══════════════════════════════════════════════════════════════

# Activar redirección HTTPS (True en producción con SSL)
SECURE_SSL_REDIRECT=False

# Cookies seguras (True en producción)
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False


# ═══════════════════════════════════════════════════════════════
#  SMTP - ENVÍO DE CORREOS
# ═══════════════════════════════════════════════════════════════

# Configuración del servidor SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Credenciales del remitente
# IMPORTANTE: Para Gmail, usar "Contraseña de Aplicación" (no la contraseña normal)
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
# Cambiar por el dominio público o IP accesible externamente
SITE_URL=http://127.0.0.1:8000
```

---

## Ejecución del Sistema

El sistema requiere **3 procesos simultáneos**. Abra 3 ventanas de terminal/consola:

### Terminal 1: Redis Server
Utilice el script automático que detecta la instalación de Redis:
```bash
venv\Scripts\activate
start_redis.bat
```

### Terminal 2: Celery Worker
Procesa la cola de generación de certificados:
```bash
venv\Scripts\activate
start_celery.bat
```

### Terminal 3: Servidor Web Django
Interfaz de usuario y API:
```bash
venv\Scripts\activate
python manage.py runserver
```

Acceder al sistema en: **http://127.0.0.1:8000**

---

## Manual de Usuario

### 1. Configuración Inicial (Una sola vez)

#### a) Definir Catálogos
Desde el panel administrativo, configure:
- **Modalidades**: Presencial, Virtual, Híbrida
- **Tipos**: Aprobación, Asistencia, Participación
- **Tipos de Evento**: Curso, Taller, Seminario, Webinar

#### b) Registrar Dirección
Cree la unidad organizacional que emitirá los certificados.
Ejemplo: "Dirección de Vinculación"

#### c) Subir Plantilla Word
Cargue el diseño `.docx` con las variables de reemplazo (ver sección Variables).

### 2. Generar Certificados

#### Paso 1: Preparar Excel de Estudiantes
Cree un archivo Excel con las siguientes columnas (el orden no importa):

| Columna | Encabezados Válidos |
|---------|---------------------|
| **Nombres** | `NOMBRES COMPLETOS`, `NOMBRE COMPLETO`, `NOMBRES`, `NOMBRE`, `ESTUDIANTE`, `PARTICIPANTE` |
| **Correo** | `CORREO ELECTRONICO`, `CORREO`, `EMAIL`, `MAIL` |

**Ejemplo:**
```
| NOMBRES COMPLETOS      | CORREO ELECTRONICO        |
|------------------------|---------------------------|
| JUAN PÉREZ LÓPEZ       | juan.perez@example.com    |
| MARÍA GARCÍA TORRES    | maria.garcia@example.com  |
```

#### Paso 2: Crear Evento
1. Ir a **Generar Certificado** → **Nuevo Evento**
2. Seleccionar Dirección y Plantilla
3. Completar datos del evento (nombre, fechas, duración)
4. Subir archivo Excel
5. Activar **Seguridad QR** (opcional)

#### Paso 3: Iniciar Generación
1. El sistema validará el Excel
2. Presionar **INICIAR GENERACIÓN**
3. Monitorear progreso en tiempo real
4. Una vez completado, descargar ZIP o enviar por correo

---

## Variables para Plantillas Word

Utilice estas etiquetas **exactamente** como aparecen (respetando espacios y mayúsculas):

### Datos del Estudiante
- `{{NOMBRES}}` - Nombre completo en mayúsculas

### Datos del Evento
- `{{TIPO}}` - Tipo de certificado (Aprobación, Asistencia)
- `{{TIPO DE EVENTO}}` - Clasificación (Curso, Taller, Seminario)
- `{{NOMBRE CURSO}}` - Nombre del evento
- `{{HORAS}}` - Duración numérica
- `{{MODALIDAD}}` - Presencial/Virtual/Híbrida
- `{{OBJETIVO DEL PROGRAMA}}` - Objetivo académico
- `{{CONTENIDO}}` - Contenido o sílabo

### Fechas
- `{{FECHA INICIO}}` - Formato: "16 de septiembre"
- `{{FECHA FIN}}` - Formato: "20 de octubre del 2025"
- `{{FECHA DE EMISION}}` - Formato: "30 días del mes de enero del 2026"

---

## Validación de Certificados (QR)

Si activó la **Seguridad QR**, cada PDF incluirá un código QR en la esquina inferior derecha.

**Para validar:**
1. Escanear el código QR con cualquier smartphone
2. Se abrirá una página pública de verificación
3. Mostrará los datos del certificado y confirmará su autenticidad

---

## Mantenimiento

### Eliminar Certificados
El sistema incluye eliminación física de archivos:
- Al presionar **ELIMINAR TODO**, se borran los PDFs del servidor
- Los registros de estudiantes se preservan para regeneración futura

### Logs del Sistema
Revisar errores en: `logs/errors.log`

---
