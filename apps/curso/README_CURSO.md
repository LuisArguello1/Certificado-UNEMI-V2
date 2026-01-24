# Documentación y Guía de Desarrollo - App Curso

Esta aplicación es el núcleo del sistema, encargada de gestionar los Cursos, cargar los Estudiantes vía Excel y definir las Plantillas.

A continuación se detallan las tareas y lineamientos técnicos para completar el módulo.

---

## 🎨 Estilo Visual (ERP Clásico Profesional)

El cliente requiere una interfaz **"ERP Clásico Profesional"**.
*   **No uses estilos de "Landing Page"** (encabezados gigantes, gradientes excesivos en toda la pantalla).
*   **Referencia**: Revisa `apps/correo/templates/correo/campaign_list.html` y `preview.html` para ver el estándar.
*   **Componentes Clave**:
    *   Tablas tipo **DataGrid**: Encabezados gris claro (`bg-gray-50`), bordes sutiles, filas hover, tipografía `Inter` o `system-ui`.
    *   **Badges**: Para estados (Activo/Inactivo), usar pills redondeados con colores suaves (e.g., fondo verde claro, texto verde oscuro).
    *   **Botones**: Claros y funcionales. `Azul/Indigo` para acciones principales, `Gris` para cancelar.

---

## 🛠 Tareas de Implementación

### 1. Procesamiento de Excel (Importante: Cédulas)
Al crear un Curso y subir el Excel de estudiantes, debes procesarlo inmediatamente para crear los registros en el modelo `Estudiante`.

**Problema Común**: Excel elimina el '0' inicial de las cédulas (e.g., `0912345678` -> `912345678`).
**Solución Técnica Suggestida**:
Al usar `pandas` o `openpyxl`, fuerza la columna de cédula como **Texto** o aplica relleno de ceros.

**Snippet de Ejemplo (Pandas):**
```python
import pandas as pd

# Leer el excel forzando 'cedula' a string
df = pd.read_excel(archivo, converters={'cedula': str})

for index, row in df.iterrows():
    cedula_raw = str(row['cedula']).strip()
    
    # Validación y Corrección (Ecuador: 10 dígitos)
    if len(cedula_raw) == 9 and cedula_raw.isdigit():
        cedula_final = '0' + cedula_raw
    else:
        cedula_final = cedula_raw
        
    # Crear estudiante
    Estudiante.objects.create(
        curso=curso_instancia,
        nombre_completo=row['nombres'],
        cedula=cedula_final,
        correo=row['email']
    )
```

### 2. Generación de Certificados (Interactivo)
Se requiere que el usuario pueda tener control sobre cómo se ve el texto en el certificado.

*   **Editor**: Implementa un editor visual (puedes reutilizar la configuración de **QuillJS** que ya está en `create_campaign.html`) para que el administrador defina el texto del certificado con variables dinámicas.
*   **Variables**: Permite insertar placeholders como `{NOMBRE_ESTUDIANTE}`, `{CEDULA}`, `{FECHA}`.
*   **Backend**: Usa una librería como `ReportLab` o `WeasyPrint` para superponer este texto HTML/Formateado sobre la imagen de fondo de la `PlantillaCertificado`.

### 3. Vistas Pendientes (CRUD)
Debes crear las vistas y templates para:
*   **Listar Cursos**: Tabla estilo ERP.
*   **Crear/Editar Curso**: Usar `CursoForm`. Aquí va la lógica del Excel.
*   **Gestionar Plantillas**: Subida de imágenes de fondo.

---

## ✅ Integraciones Ya Listas
*   **Correo Masivo**: Ya consume los estudiantes que tú crees en la base de datos.
*   **Portal Estudiantes**: Ya existe la validación de cédula y búsqueda. Solo falta que generes el PDF real en la vista `CertificateDownloadView` (actualmente es un placeholder).

## 🚀 Checklist de Entrega
- [ ] Validar importación de Excel (Ceros a la izquierda).
- [ ] Aplicar estilos consistentes (Layout `base.html`).
- [ ] Poner notificaciones (Toast/Alertas) al terminar de cargar el Excel.
- [ ] **IMPORTANTE: Feedback de Carga (Loading)**:
    - Cuando el usuario suba el Excel o cree el curso, **deshabilita el botón de guardar** y muestra un spinner o texto "Procesando...".
    - Esto evita que el usuario haga doble clic y se dupliquen datos o correos.
    - Ejemplo JS: `btn.disabled = true; btn.innerHTML = '...';`

