/**
 * Loading Overlay Manager para operaciones de certificados
 * Muestra un overlay semi-transparente con barra de progreso
 * Soporta diferentes tipos de acciones: generación, envío, individual
 */

// Tipos de acciones soportadas
const LOADING_ACTIONS = {
    GENERATE: {
        title: 'Generando Certificados',
        icon: 'fas fa-sync-alt',
        color: 'bg-black',
        successLabel: 'Generados',
        failedLabel: 'Fallidos'
    },
    SEND: {
        title: 'Enviando Correos',
        icon: 'fas fa-sync-alt',
        color: 'bg-indigo-600',
        successLabel: 'Enviados',
        failedLabel: 'Fallidos'
    },
    INDIVIDUAL: {
        title: 'Generando Certificado',
        icon: 'fas fa-sync-alt',
        color: 'bg-gray-800',
        successLabel: 'Completado',
        failedLabel: 'Error'
    }
};

class LoadingOverlayManager {
    constructor() {
        this.overlay = null;
        this.progressBar = null;
        this.progressText = null;
        this.messageText = null;
        this.titleText = null;
        this.iconElement = null;
        this.topBar = null;
        this.successLabel = null;
        this.failedLabel = null;
        this.currentAction = 'GENERATE';
        this.init();
    }

    /**
     * Inicializa el overlay en el DOM
     */
    init() {
        // Crear el overlay si no existe
        if (!document.getElementById('certificateLoadingOverlay')) {
            const overlayHTML = `
                <div id="certificateLoadingOverlay" class="fixed inset-0 z-[9999] hidden">
                    <!-- Fondo semi-transparente -->
                    <div class="absolute inset-0 bg-gray-900 bg-opacity-75 backdrop-blur-sm"></div>
                    
                    <!-- Contenido centrado -->
                    <div class="absolute inset-0 flex items-center justify-center p-4">
                        <div class="bg-white border border-gray-300 shadow-2xl rounded-sm max-w-lg w-full p-8 relative">
                            <!-- Barra superior dinámica -->
                            <div id="overlayTopBar" class="absolute top-0 left-0 right-0 bg-black h-2 transition-colors duration-300"></div>
                            
                            <!-- Icono y título -->
                            <div class="text-center mb-6">
                                <div class="inline-flex items-center justify-center h-16 w-16 rounded-full bg-gray-50 border-2 border-gray-100 mb-4">
                                    <i id="overlayIcon" class="fas fa-cog fa-spin text-black text-2xl"></i>
                                </div>
                                <h3 id="overlayTitle" class="text-sm font-black text-gray-900 uppercase tracking-tight">
                                    Procesando
                                </h3>
                            </div>
                            
                            <!-- Mensaje dinámico -->
                            <p id="overlayMessage" class="text-[10px] text-gray-500 text-center uppercase tracking-widest font-bold mb-6">
                                Procesando solicitud...
                            </p>
                            
                            <!-- Barra de progreso -->
                            <div class="w-full bg-gray-100 rounded-sm overflow-hidden h-8 border border-gray-200 relative mb-3">
                                <div id="overlayProgressBar" 
                                     class="bg-black h-full transition-all duration-500 ease-out flex items-center justify-center" 
                                     style="width: 0%">
                                    <span id="overlayProgressText" class="text-[10px] font-black text-white uppercase tracking-widest">0%</span>
                                </div>
                            </div>
                            
                            <!-- Contadores -->
                            <div class="grid grid-cols-2 gap-4 text-center">
                                <div class="bg-gray-50 p-3 rounded-sm border border-gray-100">
                                    <div id="overlaySuccessLabel" class="text-[9px] text-gray-400 uppercase tracking-widest font-bold mb-1">Exitosos</div>
                                    <div id="overlaySuccessCount" class="text-xl font-black text-black">0</div>
                                </div>
                                <div class="bg-gray-50 p-3 rounded-sm border border-gray-100">
                                    <div id="overlayFailedLabel" class="text-[9px] text-gray-400 uppercase tracking-widest font-bold mb-1">Fallidos</div>
                                    <div id="overlayFailedCount" class="text-xl font-black text-red-600">0</div>
                                </div>
                            </div>
                            
                            <!-- Advertencia -->
                            <div class="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded-sm">
                                <p class="text-[9px] text-yellow-700 text-center uppercase tracking-widest font-bold">
                                    <i class="fas fa-exclamation-triangle mr-1"></i>
                                    No cierre ni recargue esta página
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Insertar en el DOM
            document.body.insertAdjacentHTML('beforeend', overlayHTML);
        }

        // Obtener referencias
        this.overlay = document.getElementById('certificateLoadingOverlay');
        this.progressBar = document.getElementById('overlayProgressBar');
        this.progressText = document.getElementById('overlayProgressText');
        this.messageText = document.getElementById('overlayMessage');
        this.titleText = document.getElementById('overlayTitle');
        this.iconElement = document.getElementById('overlayIcon');
        this.topBar = document.getElementById('overlayTopBar');
        this.successCount = document.getElementById('overlaySuccessCount');
        this.failedCount = document.getElementById('overlayFailedCount');
        this.successLabel = document.getElementById('overlaySuccessLabel');
        this.failedLabel = document.getElementById('overlayFailedLabel');
    }

    /**
     * Configura la apariencia según el tipo de acción
     * @param {string} actionType - Tipo de acción: 'GENERATE', 'SEND', 'INDIVIDUAL'
     */
    setAction(actionType) {
        const action = LOADING_ACTIONS[actionType] || LOADING_ACTIONS.GENERATE;
        this.currentAction = actionType;

        if (this.titleText) {
            this.titleText.textContent = action.title;
        }

        if (this.iconElement) {
            // Remover clases de icono anteriores y añadir la nueva
            this.iconElement.className = `fas ${action.icon} fa-spin text-black text-2xl`;
        }

        if (this.topBar) {
            // Remover clases de color anteriores
            this.topBar.className = `absolute top-0 left-0 right-0 ${action.color} h-2 transition-colors duration-300`;
        }

        if (this.progressBar) {
            // Actualizar color de la barra de progreso
            this.progressBar.className = `${action.color} h-full transition-all duration-500 ease-out flex items-center justify-center`;
        }

        if (this.successLabel) {
            this.successLabel.textContent = action.successLabel;
        }

        if (this.failedLabel) {
            this.failedLabel.textContent = action.failedLabel;
        }
    }

    /**
     * Obtiene el tipo de acción actual
     * @returns {string} Tipo de acción actual
     */
    getAction() {
        return this.currentAction;
    }

    /**
     * Muestra el overlay
     * @param {string} message - Mensaje inicial a mostrar
     * @param {string} actionType - Tipo de acción: 'GENERATE', 'SEND', 'INDIVIDUAL'
     */
    show(message = 'Iniciando proceso...', actionType = 'GENERATE') {
        if (this.overlay) {
            this.setAction(actionType);
            this.updateMessage(message);
            this.updateProgress(0, 0, 0);
            this.overlay.classList.remove('hidden');
            document.body.style.overflow = 'hidden'; // Bloquear scroll
        }
    }

    /**
     * Oculta el overlay
     */
    hide() {
        if (this.overlay) {
            this.overlay.classList.add('hidden');
            document.body.style.overflow = ''; // Restaurar scroll
        }
    }

    /**
     * Actualiza el mensaje
     * @param {string} message - Nuevo mensaje
     */
    updateMessage(message) {
        if (this.messageText) {
            this.messageText.textContent = message;
        }
    }

    /**
     * Actualiza la barra de progreso
     * @param {number} progress - Porcentaje de progreso (0-100)
     * @param {number} success - Cantidad de exitosos
     * @param {number} failed - Cantidad de fallidos
     */
    updateProgress(progress, success = 0, failed = 0) {
        if (this.progressBar && this.progressText) {
            this.progressBar.style.width = `${progress}%`;
            this.progressText.textContent = `${progress}%`;
        }

        if (this.successCount) {
            this.successCount.textContent = success;
        }

        if (this.failedCount) {
            this.failedCount.textContent = failed;
        }
    }
}

// Crear instancia global
window.loadingOverlay = new LoadingOverlayManager();
