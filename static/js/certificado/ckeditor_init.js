/**
 * Inicialización de CKEditor 5 para campos de texto enriquecido.
 * 
 * Configura editores en los campos:
 * - Objetivo del Programa
 * - Contenido Programático
 * 
 * Características:
 * - Toolbar con formato básico, listas con sangrías y tablas
 * - Estilos personalizados para listas visibles
 * - Soporte para jerarquías (indent/outdent)
 * - Limpieza automática de HTML al submit
 */

// Configuración de CKEditor para campos de certificado
const CKEDITOR_CONFIG = {
    toolbar: {
        items: [
            'bold', 'italic', 'underline', '|',
            'alignment', '|',
            'bulletedList', 'numberedList', '|',
            'outdent', 'indent', '|',
            'insertTable', '|',
            'specialCharacters', '|',
            'undo', 'redo', '|',
            'removeFormat'
        ],
        shouldNotGroupWhenFull: true
    },
    alignment: {
        options: ['left', 'center', 'right', 'justify']
    },
    // Plugins a remover del Super Build (no necesarios)
    removePlugins: [
        'AIAssistant', 'CKBox', 'CKFinder', 'EasyImage', 'RealTimeCollaborativeComments',
        'RealTimeCollaborativeTrackChanges', 'RealTimeCollaborativeRevisionHistory',
        'PresenceList', 'Comments', 'TrackChanges', 'TrackChangesData', 'RevisionHistory',
        'Pagination', 'WProofreader', 'MathType', 'SlashCommand', 'Template', 'DocumentOutline',
        'FormatPainter', 'TableOfContents', 'PasteFromOfficeEnhanced', 'CaseChange'
    ],
    // Configuración para preservar párrafos vacíos (Shift+Enter = <br>, Enter = nuevo párrafo)
    htmlSupport: {
        allow: [
            { name: 'p', styles: true, classes: true },
            { name: 'br' }
        ]
    },
    list: {
        properties: {
            styles: true,
            startIndex: true,
            reversed: true
        }
    },
    table: {
        contentToolbar: [
            'tableColumn',
            'tableRow',
            'mergeTableCells',
            'tableProperties',
            'tableCellProperties'
        ],
        tableProperties: {
            borderColors: [
                { color: '#000000', label: 'Negro' },
                { color: '#374151', label: 'Gris oscuro' },
                { color: '#6b7280', label: 'Gris' },
                { color: '#3b82f6', label: 'Azul' },
                { color: '#10b981', label: 'Verde' },
                { color: '#f59e0b', label: 'Amarillo' },
                { color: '#ef4444', label: 'Rojo' }
            ],
            backgroundColors: [
                { color: '#ffffff', label: 'Blanco' },
                { color: '#f9fafb', label: 'Gris claro' },
                { color: '#f3f4f6', label: 'Gris' },
                { color: '#dbeafe', label: 'Azul claro' },
                { color: '#d1fae5', label: 'Verde claro' },
                { color: '#fef3c7', label: 'Amarillo claro' },
                { color: '#fee2e2', label: 'Rojo claro' }
            ]
        },
        tableCellProperties: {
            borderColors: [
                { color: '#000000', label: 'Negro' },
                { color: '#374151', label: 'Gris oscuro' },
                { color: '#6b7280', label: 'Gris' },
                { color: '#3b82f6', label: 'Azul' }
            ],
            backgroundColors: [
                { color: '#ffffff', label: 'Blanco' },
                { color: '#f9fafb', label: 'Gris claro' },
                { color: '#f3f4f6', label: 'Gris' },
                { color: '#dbeafe', label: 'Azul claro' },
                { color: '#d1fae5', label: 'Verde claro' },
                { color: '#fef3c7', label: 'Amarillo claro' }
            ]
        }
    },
    language: 'es',
    placeholder: 'Escriba aquí el contenido...'
};

// Almacenar instancias de editores
const editorInstances = {};

/**
 * Inicializa CKEditor en un campo específico
 * @param {string} selector - Selector CSS del textarea
 * @param {string} editorKey - Key única para almacenar la instancia
 * @returns {Promise<void>}
 */
async function initCKEditor(selector, editorKey) {
    try {
        const element = document.querySelector(selector);
        
        if (!element) {
            console.warn(`Elemento no encontrado: ${selector}`);
            return;
        }

        // Si ya existe una instancia, destruirla primero
        if (editorInstances[editorKey]) {
            await editorInstances[editorKey].destroy();
            delete editorInstances[editorKey];
        }

        // Crear nueva instancia (Super Build usa CKEDITOR.ClassicEditor)
        const EditorClass = window.CKEDITOR?.ClassicEditor || window.ClassicEditor;
        const editor = await EditorClass.create(element, CKEDITOR_CONFIG);
        
        // Guardar instancia
        editorInstances[editorKey] = editor;
        
        // Configurar actualización automática del textarea original
        editor.model.document.on('change:data', () => {
            element.value = editor.getData();
        });

        console.log(`CKEditor inicializado: ${editorKey}`);

    } catch (error) {
        console.error(`Error inicializando CKEditor en ${selector}:`, error);
        
        // Fallback: mostrar textarea normal
        const element = document.querySelector(selector);
        if (element) {
            element.classList.remove('ckeditor-target');
            element.style.display = 'block';
        }
    }
}

/**
 * Limpia y valida el HTML antes de enviar el formulario
 * @param {HTMLFormElement} form - Formulario a validar
 */
function cleanHTMLBeforeSubmit(form) {
    // Actualizar textareas con datos de los editores
    Object.entries(editorInstances).forEach(([key, editor]) => {
        const element = editor.sourceElement;
        if (element) {
            element.value = editor.getData();
        }
    });
}

/**
 * Inicializa todos los editores CKEditor en la página
 */
async function initAllEditors() {
    // Buscar todos los textareas con la clase 'ckeditor-target'
    const targets = document.querySelectorAll('textarea.ckeditor-target');
    
    if (targets.length === 0) {
        console.info('No se encontraron campos para CKEditor');
        return;
    }

    console.log(`Inicializando ${targets.length} editores CKEditor...`);

    // Inicializar cada editor
    for (const target of targets) {
        const editorType = target.dataset.editorType || target.id;
        await initCKEditor(`#${target.id}`, editorType);
    }

    // Configurar limpieza al submit del formulario
    const form = targets[0].closest('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            cleanHTMLBeforeSubmit(form);
        });
    }
}

/**
 * Destruye todos los editores (útil para cleanup)
 */
async function destroyAllEditors() {
    for (const [key, editor] of Object.entries(editorInstances)) {
        try {
            await editor.destroy();
            delete editorInstances[key];
        } catch (error) {
            console.error(`Error destruyendo editor ${key}:`, error);
        }
    }
}

// Auto-inicialización cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAllEditors);
} else {
    // DOM ya está listo
    initAllEditors();
}

// Cleanup al salir de la página
window.addEventListener('beforeunload', () => {
    destroyAllEditors();
});

// Exportar funciones para uso externo
window.CKEditorManager = {
    init: initAllEditors,
    destroy: destroyAllEditors,
    instances: editorInstances
};
