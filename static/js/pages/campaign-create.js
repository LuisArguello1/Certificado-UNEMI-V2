document.addEventListener("DOMContentLoaded", function () {

    // Configuración de títulos para accesibilidad
    const toolbarOptions = [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'align': [] }],
        [{ 'list': 'ordered' }, { 'list': 'bullet' }],
        [{ 'color': [] }, { 'background': [] }],
        ['link', 'image', 'clean'] // Added 'image' to toolbar explicitly if missing, though it was in default options logic usually
    ];

    // Inicializar Quill
    var quill = new Quill('#editor-container', {
        theme: 'snow',
        placeholder: 'Escriba el contenido del correo aquí...',
        modules: {
            toolbar: toolbarOptions,
            clipboard: {
                matchVisual: false // Improves pasting behavior
            }
        }
    });

    // Custom Image Handler for Paste (Optional but helper)
    // Quill by default handles base64 paste for images.
    // If user wants to paste *files* (not supported by default in v1), we need a handler.
    // implementing a basic matcher for images.

    // Añadir títulos manualmente a los botones
    const tooltips = {
        '.ql-bold': 'Negrita',
        '.ql-italic': 'Cursiva',
        '.ql-underline': 'Subrayado',
        '.ql-strike': 'Tachado',
        '.ql-list[value="ordered"]': 'Lista numerada',
        '.ql-list[value="bullet"]': 'Lista con viñetas',
        '.ql-link': 'Insertar enlace',
        '.ql-image': 'Insertar imagen (URL o Copiar/Pegar)',
        '.ql-clean': 'Borrar formato',
        '.ql-align': 'Alineación',
        '.ql-color': 'Color de texto',
        '.ql-background': 'Color de fondo'
    };

    for (const [selector, title] of Object.entries(tooltips)) {
        const button = document.querySelector(selector);
        if (button) button.setAttribute('title', title);
    }

    // Vincular contenido de Quill al input oculto
    // El ID se pasa como data-attribute o variable global, pero para mantenerlo limpio
    // buscaremos el input por nombre o selector genérico si es posible,
    // o pasaremos el ID desde el HTML al script via data-attribute en el container.

    const container = document.getElementById('editor-container');
    const inputId = container.getAttribute('data-input-id');
    var messageInput = document.getElementById(inputId);

    if (messageInput) {
        messageInput.style.display = 'none';

        // Cargar contenido inicial si existe
        if (messageInput.value) {
            quill.root.innerHTML = messageInput.value;
        }

        // Función para sincronizar contenido de Quill al input oculto
        function syncQuillContent() {
            let htmlContent = quill.root.innerHTML;

            // Limpiar contenido vacío (solo <p><br></p> significa vacío)
            if (htmlContent === '<p><br></p>') {
                htmlContent = '';
            }

            // Reemplazos de alineación para soporte email
            htmlContent = htmlContent
                .replace(/class="ql-align-center"/g, 'style="text-align: center; display: block;"')
                .replace(/class="ql-align-right"/g, 'style="text-align: right; display: block;"')
                .replace(/class="ql-align-justify"/g, 'style="text-align: justify; display: block;"');

            messageInput.value = htmlContent;

            // Debug en consola
            console.log('Contenido sincronizado:', htmlContent.substring(0, 100));
        }

        // Sincronizar cuando cambia el contenido (en tiempo real)
        quill.on('text-change', function () {
            syncQuillContent();
        });

        // Sincronizar antes de enviar el formulario (crítico)
        const form = document.querySelector('form');
        form.addEventListener('submit', function (e) {
            syncQuillContent();
            console.log('Formulario enviado con mensaje:', messageInput.value.substring(0, 100));
        });
    }
});

// === COURSE SELECTION MODAL LOGIC ===
window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

window.selectCourse = function (id, name, count, previewUrl) {
    // 1. Update Hidden Input
    const input = document.getElementById('id_course');
    if (input) input.value = id;

    // 2. Update Visual Details
    const nameEl = document.getElementById('selected-course-name');
    const countEl = document.getElementById('selected-course-count');

    if (nameEl) nameEl.textContent = name;
    if (countEl) countEl.textContent = count;

    // 3. Handle PDF Preview Button
    const previewContainer = document.getElementById('pdf-preview-link');
    const previewBtn = document.getElementById('btn-view-pdf');

    // previewUrl can be "None" string if coming from template parsing sometimes, or empty logic
    if (previewUrl && previewUrl !== 'None' && previewUrl !== '') {
        previewContainer.classList.remove('hidden');
        previewBtn.href = previewUrl;
    } else {
        previewContainer.classList.add('hidden');
        previewBtn.href = '#';
    }

    // 4. Toggle States
    const noState = document.getElementById('no-course-state');
    const selectedState = document.getElementById('course-selected-state');

    if (noState) noState.classList.add('hidden');
    if (selectedState) selectedState.classList.remove('hidden');

    // 5. Close Modal
    closeModal('courseModal');
}
