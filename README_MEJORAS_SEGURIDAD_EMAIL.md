# Guía de Implementación: Mejoras de Seguridad y Configuración de Email

Este documento detalla los pasos para implementar las mejoras de seguridad (QR) y cómo configurar correctamente los límites de envío de correos.

---

## 1. Configuración de Envío de Correos (Gmail Rate Limit)

### Situación Actual
Actualmente tienes configuradas las variables en tu archivo `.env`:
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_DAILY_LIMIT=400       # Límite total diario (usado por el modelo)
EMAIL_RATE_LIMIT_SECONDS=2  # Segundos entre correos (referencia)
EMAIL_BATCH_SIZE=10         # Referencia para lotes
```

Sin embargo, el **Rate Limit** real que protege tu cuenta de Gmail está definido en el código de la tarea de Celery (`tasks.py`) y **no está leyendo directamente la variable del .env**.

### Cómo Resolverlo (Hacer que respete el .env)

Para que el sistema "se adapte" automáticamente a lo que pongas en el `.env`, debes modificar el archivo `apps/certificado/tasks.py`.

**Archivo:** `apps/certificado/tasks.py` (Línea ~110)

**Código Actual:**
```python
@shared_task(bind=True, max_retries=5, rate_limit='30/m', ...) 
def send_certificate_email_task(self, certificado_id: int):
```
*El valor `'30/m'` está fijo (hardcoded).*

**Código Sugerido (Dinámico):**
Desafortunadamente, el decorador `@shared_task` se evalúa al iniciar el sistema, por lo que pasarle una variable de entorno directamente es complejo. 

**La Solución Recomendada** es mantenerlo manual o cambiarlo a `rate_limit='15/m'` directamente en el código si notas bloqueos. 
*Nota: `30/m` (1 cada 2 segundos) es el estándar seguro para Gmail. Cambiarlo a más velocidad podría bloquearte.*

Si deseas estrictamente cambiarlo, edita manualmente el valor `'30/m'` en `tasks.py` cada vez que quieras ajustar la velocidad.

---

## 2. Implementación de Seguridad Anti-Falsificación (Código QR)

Para evitar la clonación de certificados, implementaremos:
1.  **UUID**: Un código único irrepetible.
2.  **QR**: Una imagen en el certificado que apunta a la validación.
3.  **Validación Web**: Una página pública que confirma la veracidad.

### Prerrequisitos
Ya tienes instaladas las librerías necesarias (`qrcode` y `pillow`) en tu `requirements.txt`.

### Paso 1: Modificar el Modelo `Certificado`

Añadir un campo UUID en `apps/certificado/models.py`:

```python
import uuid

class Certificado(models.Model):
    # ... campos existentes ...
    # Nuevo campo para validación
    uuid_validacion = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # ...
```

*Recuerda ejecutar `python manage.py makemigrations` y `migrate` después.*

### Paso 2: Crear la Vista de Validación

En `apps/certificado/views/public_views.py` (crear si no existe):

```python
from django.shortcuts import render, get_object_or_404
from ..models import Certificado

def validar_certificado(request, uuid):
    certificado = get_object_or_404(Certificado, uuid_validacion=uuid)
    
    context = {
        'certificado': certificado,
        'valido': True,
        'estudiante': certificado.estudiante.nombres_completos,
        'curso': certificado.evento.nombre_evento,
        'fecha': certificado.fecha_emision
    }
    return render(request, 'certificado/public/validacion.html', context)
```

### Paso 3: Generar e Insertar el QR en el PDF

En `apps/certificado/services/template_service.py`, modificar la generación para incluir el QR.

1.  **Generar imagen QR temporal:**
    ```python
    import qrcode
    
    def generar_qr_temporal(url_validacion):
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(url_validacion)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        path = f"/tmp/qr_{uuid.uuid4()}.png"
        img.save(path)
        return path
    ```

2.  **Insertar en DOCX:**
    Necesitas tener un "placeholder" (una imagen de ejemplo con Texto Alt específico, ej: `{{QR_CODE}}`) en tu plantilla Word (`.docx`).
    
    Luego, usamos `python-docx` para reemplazar esa imagen:
    
    ```python
    # Lógica simplificada
    for shape in doc.inline_shapes:
        if shape.alternative_text == '{{QR_CODE}}':
            shape._inline.graphic.graphicData.pic.blipFill.blip.embed = nuevo_rId
    ```
    *(Esta parte es técnica y requiere manipular el XML del docx, o simplemente insertar la imagen al final del documento).*

### Paso 4: URL de Validación

Asegúrate de que la URL en el QR sea accesible públicamente:
`https://tudominio.com/validar/{certificado.uuid_validacion}/`

---

### Resumen
Siguiendo estos pasos tendrás un sistema robusto:
1.  **Envío Seguro**: Manteniendo el rate limit de Celery (o ajustándolo manualmente en `tasks.py`).
2.  **Certificados Infalsificables**: Gracias al UUID y validación cruzada por QR.
