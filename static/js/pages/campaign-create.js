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

        if (messageInput.value) {
            quill.root.innerHTML = messageInput.value;
        }

        document.querySelector('form').onsubmit = function () {
            let htmlContent = quill.root.innerHTML;

            // Reemplazos de alineación para soporte email
            htmlContent = htmlContent
                .replace(/class="ql-align-center"/g, 'style="text-align: center; display: block;"')
                .replace(/class="ql-align-right"/g, 'style="text-align: right; display: block;"')
                .replace(/class="ql-align-justify"/g, 'style="text-align: justify; display: block;"');

            messageInput.value = htmlContent;
        };
    }
});
