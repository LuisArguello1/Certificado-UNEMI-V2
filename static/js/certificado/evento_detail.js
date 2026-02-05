/**
 * JavaScript para la vista de detalle de evento de certificados
 * Maneja la generación, edición, eliminación y envío de certificados
 */

// Variables globales (csrftoken se define en el template)
let pollInterval = null;

// Variables para polling inteligente (optimización)
let lastStateHash = null;
let noChangeCount = 0;
let currentPollInterval = 1000;

// Estado para modales Alpine
const modalState = {
    editModal: {
        isOpen: false,
        estudianteId: null,
        nombre: '',
        correo: ''
    },
    deleteModal: {
        isOpen: false,
        estudianteId: null,
        nombre: ''
    },
    createModal: {
        isOpen: false,
        nombre: '',
        correo: ''
    }
};

/**
 * Muestra un toast de notificación
 * @param {string} msg - Mensaje a mostrar
 */
function showToast(msg) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');
    if (toast && toastMsg) {
        toastMsg.textContent = msg;
        toast.classList.remove('translate-y-32', 'opacity-0');
        setTimeout(() => toast.classList.add('translate-y-32', 'opacity-0'), 4000);
    }
}

/**
 * Abre el modal de edición de estudiante
 * @param {number} estId - ID del estudiante
 * @param {string} nombre - Nombre completo actual
 * @param {string} correo - Correo electrónico actual
 */
function openEditModal(estId, nombre, correo) {
    modalState.editModal.isOpen = true;
    modalState.editModal.estudianteId = estId;
    modalState.editModal.nombre = nombre;
    modalState.editModal.correo = correo;

    // Actualizar campos del formulario
    const nombreInput = document.getElementById('editNombre');
    const correoInput = document.getElementById('editCorreo');
    if (nombreInput) nombreInput.value = nombre;
    if (correoInput) correoInput.value = correo;

    // Mostrar modal
    const modal = document.getElementById('editModal');
    if (modal) modal.classList.remove('hidden');
}

/**
 * Cierra el modal de edición
 */
function closeEditModal() {
    modalState.editModal.isOpen = false;
    const modal = document.getElementById('editModal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Guarda los cambios del modal de edición
 */
function saveEditModal() {
    const nombreInput = document.getElementById('editNombre');
    const correoInput = document.getElementById('editCorreo');

    if (!nombreInput || !correoInput) return;

    const nombre = nombreInput.value.trim();
    const correo = correoInput.value.trim();

    // Validación básica
    if (!nombre || !correo) {
        showToast("TODOS LOS CAMPOS SON REQUERIDOS");
        return;
    }

    // Validación de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(correo)) {
        showToast("FORMATO DE CORREO INVÁLIDO");
        return;
    }

    const formData = new FormData();
    formData.append('action', 'update_student');
    formData.append('estudiante_id', modalState.editModal.estudianteId);
    formData.append('nombre', nombre);
    formData.append('correo', correo);
    formData.append('csrfmiddlewaretoken', csrftoken);

    fetch('', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(data.message.toUpperCase());
                closeEditModal();
                // Actualizar la UI
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showToast(data.error.toUpperCase());
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast("ERROR AL GUARDAR CAMBIOS");
        });
}

/**
 * Abre el modal de creación de estudiante
 */
function openCreateModal() {
    modalState.createModal.isOpen = true;

    // Limpiar campos
    const nombreInput = document.getElementById('createNombre');
    const correoInput = document.getElementById('createCorreo');
    if (nombreInput) nombreInput.value = '';
    if (correoInput) correoInput.value = '';

    // Mostrar modal
    const modal = document.getElementById('createModal');
    if (modal) modal.classList.remove('hidden');
}

/**
 * Cierra el modal de creación
 */
function closeCreateModal() {
    modalState.createModal.isOpen = false;
    const modal = document.getElementById('createModal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Guarda el nuevo estudiante
 */
function saveCreateModal() {
    const nombreInput = document.getElementById('createNombre');
    const correoInput = document.getElementById('createCorreo');

    if (!nombreInput || !correoInput) return;

    const nombre = nombreInput.value.trim();
    const correo = correoInput.value.trim();

    // Validación básica
    if (!nombre || !correo) {
        showToast("TODOS LOS CAMPOS SON REQUERIDOS");
        return;
    }

    // Validación de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(correo)) {
        showToast("FORMATO DE CORREO INVÁLIDO");
        return;
    }

    const formData = new FormData();
    formData.append('action', 'create_student');
    formData.append('nombre', nombre);
    formData.append('correo', correo);
    formData.append('csrfmiddlewaretoken', csrftoken);

    // Deshabilitar botón para evitar doble envío
    const saveBtn = document.getElementById('btnSaveCreate');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> GUARDANDO...';
    }

    fetch(window.location.pathname, { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(data.message.toUpperCase());
                closeCreateModal();
                // Recargar para mostrar el nuevo estudiante
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showToast(data.error.toUpperCase());
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = 'GUARDAR';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast("ERROR AL CREAR ESTUDIANTE");
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = 'GUARDAR';
            }
        });
}

/**
 * Abre el modal de confirmación de eliminación
 * @param {number} estId - ID del estudiante
 * @param {string} nombre - Nombre completo del estudiante
 */
function openDeleteModal(estId, nombre) {
    modalState.deleteModal.isOpen = true;
    modalState.deleteModal.estudianteId = estId;
    modalState.deleteModal.nombre = nombre;

    // Actualizar mensaje
    const deleteMsg = document.getElementById('deleteStudentName');
    if (deleteMsg) deleteMsg.textContent = nombre;

    // Mostrar modal
    const modal = document.getElementById('deleteModal');
    if (modal) modal.classList.remove('hidden');
}

/**
 * Cierra el modal de eliminación
 */
function closeDeleteModal() {
    modalState.deleteModal.isOpen = false;
    const modal = document.getElementById('deleteModal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Confirma y ejecuta la eliminación del estudiante
 */
function confirmDeleteModal() {
    const formData = new FormData();
    formData.append('action', 'delete_student');
    formData.append('estudiante_id', modalState.deleteModal.estudianteId);
    formData.append('csrfmiddlewaretoken', csrftoken);

    fetch('', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast("ESTUDIANTE ELIMINADO");
                closeDeleteModal();

                // Animar y eliminar fila
                const row = document.getElementById(`row-${modalState.deleteModal.estudianteId}`);
                if (row) {
                    row.classList.add('opacity-0', 'scale-95', 'transition-all', 'duration-300');
                    setTimeout(() => row.remove(), 300);
                }
            } else {
                showToast(data.error.toUpperCase());
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast("ERROR AL ELIMINAR ESTUDIANTE");
        });
}

/**
 * Genera un certificado individual
 * @param {number} estId - ID del estudiante
 */
function generateIndividual(estId) {
    // Mostrar loading overlay con tipo INDIVIDUAL
    if (window.loadingOverlay) {
        window.loadingOverlay.show('Iniciando generación individual...', 'INDIVIDUAL');
    }

    const formData = new FormData();
    formData.append('action', 'generate_individual');
    formData.append('estudiante_id', estId);
    formData.append('csrfmiddlewaretoken', csrftoken);

    showToast("INICIANDO GENERACIÓN INDIVIDUAL...");

    fetch('', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast("PROCESANDO CERTIFICADO");
                if (window.loadingOverlay) {
                    window.loadingOverlay.updateMessage('Generando certificado. Espere por favor...');
                }
                startIndividualPolling(data.certificado_id);
            } else {
                showToast(data.error.toUpperCase());
                if (window.loadingOverlay) {
                    window.loadingOverlay.hide();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast("ERROR AL INICIAR GENERACIÓN");
            if (window.loadingOverlay) {
                window.loadingOverlay.hide();
            }
        });
}

/**
 * Polling específico para un certificado individual
 */
function startIndividualPolling(certId) {
    if (pollInterval) clearInterval(pollInterval);

    const checkStatus = () => {
        const formData = new FormData();
        formData.append('action', 'get_certificate_status');
        formData.append('certificado_id', certId);
        formData.append('csrfmiddlewaretoken', csrftoken);

        fetch('', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (data.is_complete) {
                        clearInterval(pollInterval);

                        if (data.status === 'failed') {
                            showToast("ERROR: " + (data.error_mensaje || 'Falló la generación'));
                            if (window.loadingOverlay) window.loadingOverlay.hide();
                        } else {
                            showToast("CERTIFICADO GENERADO CON ÉXITO");
                            if (window.loadingOverlay) {
                                window.loadingOverlay.updateMessage('¡Completado! Recargando...');
                            }
                            setTimeout(() => location.reload(), 1000);
                        }
                    }
                    // Si sigue en pending, seguimos esperando
                }
            })
            .catch(error => console.error('Error polling individual:', error));
    };

    checkStatus();
    pollInterval = setInterval(checkStatus, 2000);
}

/**
 * Inicia la generación masiva de certificados
 */
function startGeneration() {
    const btn = document.getElementById('btnGenerate');
    if (btn) {
        btn.disabled = true;
        btn.classList.add('opacity-50');
        const icon = btn.querySelector('.fa-sync-alt');
        if (icon) icon.classList.add('fa-spin');
    }

    // Mostrar loading overlay con tipo GENERATE
    if (window.loadingOverlay) {
        window.loadingOverlay.show('Iniciando generación masiva de certificados...', 'GENERATE');
    }

    const formData = new FormData();
    formData.append('action', 'start_generation');
    formData.append('csrfmiddlewaretoken', csrftoken);

    fetch('', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast("GENERACIÓN POR LOTES INICIADA");

                if (window.loadingOverlay) {
                    window.loadingOverlay.updateMessage('Generando certificados. Por favor NO cierre ni recargue esta página...');
                }

                startPolling('GENERATE');
            } else {
                showToast(data.error.toUpperCase());
                if (btn) {
                    btn.disabled = false;
                    btn.classList.remove('opacity-50');
                    const icon = btn.querySelector('i');
                    if (icon) icon.classList.remove('fa-spin');
                }
                if (window.loadingOverlay) {
                    window.loadingOverlay.hide();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast("ERROR AL INICIAR GENERACIÓN");
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('opacity-50');
            }
            if (window.loadingOverlay) {
                window.loadingOverlay.hide();
            }
        });
}

/**
 * Inicia el polling para monitorear el progreso
 * OPTIMIZADO: Implementa backoff adaptativo y detección de cambios
 * 
 * @param {string} actionType - Tipo de acción: 'GENERATE' o 'SEND'
 */
function startPolling(actionType = 'GENERATE') {
    if (pollInterval) clearInterval(pollInterval);

    // Reiniciar estado del polling inteligente
    lastStateHash = null;
    noChangeCount = 0;
    currentPollInterval = 1000;

    // Mensajes según el tipo de acción
    const messages = {
        GENERATE: {
            processing: 'Generando certificados',
            complete: '¡Generación completada! Recargando página...'
        },
        SEND: {
            processing: 'Enviando correos electrónicos',
            complete: '¡Envío completado! Recargando página...'
        }
    };

    const currentMessages = messages[actionType] || messages.GENERATE;

    // Función helper para obtener y actualizar progreso
    const checkProgress = () => {
        const formData = new FormData();
        formData.append('action', 'get_progress');
        formData.append('csrfmiddlewaretoken', csrftoken);

        fetch('', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // OPTIMIZACIÓN: Detectar si hubo cambios usando hash
                    const hasChanged = lastStateHash !== data.state_hash;

                    if (hasChanged) {
                        // HAY CAMBIOS: resetear contador y mantener intervalo rápido
                        noChangeCount = 0;
                        const previousInterval = currentPollInterval;
                        currentPollInterval = 1000;

                        // Actualizar UI solo cuando hay cambios
                        updateProgressUI(data, currentMessages, actionType);

                        // Guardar nuevo hash
                        lastStateHash = data.state_hash;

                        // Si cambiamos el intervalo, reiniciar polling
                        if (previousInterval !== currentPollInterval) {
                            clearInterval(pollInterval);
                            pollInterval = setInterval(checkProgress, currentPollInterval);
                        }
                    } else {
                        // NO HAY CAMBIOS: incrementar intervalo (backoff adaptativo)
                        noChangeCount++;

                        let newInterval = currentPollInterval;

                        // Backoff adaptativo
                        if (noChangeCount >= 10) {
                            newInterval = 5000;  // 5 segundos después de 10 intentos sin cambio
                        } else if (noChangeCount >= 5) {
                            newInterval = 3000;  // 3 segundos después de 5 intentos
                        } else if (noChangeCount >= 3) {
                            newInterval = 2000;  // 2 segundos después de 3 intentos
                        }

                        // Si el intervalo cambió, reiniciar polling con nuevo intervalo
                        if (newInterval !== currentPollInterval) {
                            currentPollInterval = newInterval;
                            clearInterval(pollInterval);
                            pollInterval = setInterval(checkProgress, currentPollInterval);
                            console.log(`[Polling] Sin cambios detectados. Intervalo ajustado a ${currentPollInterval}ms`);
                        }
                    }

                    // Si está completo, detener polling y recargar
                    if (data.is_complete) {
                        clearInterval(pollInterval);
                        if (window.loadingOverlay) {
                            window.loadingOverlay.updateMessage(currentMessages.complete);
                        }
                        setTimeout(() => {
                            location.reload();
                        }, 1500);
                    }
                }
            })
            .catch(error => {
                console.error('Error al consultar progreso:', error);
            });
    };

    // Ejecutar inmediatamente la primera vez
    checkProgress();

    // Luego continuar con intervalo inicial de 1 segundo
    pollInterval = setInterval(checkProgress, currentPollInterval);
}

/**
 * Actualiza la UI con el progreso actual
 * Función helper extraída para evitar duplicación de código
 */
function updateProgressUI(data, messages, actionType) {
    const progress = data.progress || 0;

    // Actualizar barra de progreso en la página
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const countSuccess = document.getElementById('countSuccess');
    const countFailed = document.getElementById('countFailed');

    if (progressBar) progressBar.style.width = progress + '%';
    if (progressPercent) progressPercent.textContent = progress + '%';
    if (countSuccess) countSuccess.textContent = data.exitosos;
    if (countFailed) countFailed.textContent = data.fallidos;

    // Actualizar loading overlay si está activo
    if (window.loadingOverlay) {
        // Si el overlay está oculto pero estamos procesando, mostrarlo (caso recarga de página)
        if (data.status === 'processing' && window.loadingOverlay.overlay.classList.contains('hidden')) {
            window.loadingOverlay.show(`${messages.processing}...`, actionType);
        }

        // Actualizar mensaje con progreso si está visible
        if (!window.loadingOverlay.overlay.classList.contains('hidden')) {
            window.loadingOverlay.updateMessage(
                `${messages.processing}: ${data.exitosos} de ${data.total} completados (${progress}%)`
            );
            window.loadingOverlay.updateProgress(progress, data.exitosos, data.fallidos);
        }
    }
}

/**
 * Abre el modal de confirmación de envío masivo
 */
function openSendModal() {
    const modal = document.getElementById('sendModal');
    if (modal) modal.classList.remove('hidden');
}

/**
 * Cierra el modal de envío masivo
 */
function closeSendModal() {
    const modal = document.getElementById('sendModal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Confirma y ejecuta el envío masivo de certificados
 */
function confirmSend() {
    closeSendModal();

    const formData = new FormData();
    formData.append('action', 'start_sending');
    formData.append('csrfmiddlewaretoken', csrftoken);

    // Mostrar loading overlay con tipo SEND
    if (window.loadingOverlay) {
        window.loadingOverlay.show('Iniciando envío masivo de correos...', 'SEND');
    }

    fetch('', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(data.message.toUpperCase());

                if (window.loadingOverlay) {
                    window.loadingOverlay.updateMessage('Enviando correos electrónicos. Por favor espere...');
                }

                startPolling('SEND');
            } else {
                showToast(data.error.toUpperCase());
                if (window.loadingOverlay) {
                    window.loadingOverlay.hide();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast("ERROR AL INICIAR ENVÍO");
            if (window.loadingOverlay) {
                window.loadingOverlay.hide();
            }
        });
}

/**
 * Alterna el estado de inclusión de QR en los certificados
 */
function toggleQrSeguridad() {
    const toggle = document.getElementById('toggleQrInput');
    const statusText = document.getElementById('qrStatusText');
    if (!toggle || !statusText) return;

    const isChecked = toggle.checked;

    // Optimistic UI update
    statusText.textContent = isChecked ? 'ACTIVO' : 'INACTIVO';

    const formData = new FormData();
    formData.append('action', 'toggle_qr');
    formData.append('incluir_qr', isChecked ? 'true' : 'false');
    formData.append('csrfmiddlewaretoken', csrftoken);

    fetch('', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast("SEGURIDAD QR ACTUALIZADA");
            } else {
                showToast("ERROR AL ACTUALIZAR");
                // Revert
                toggle.checked = !isChecked;
                statusText.textContent = !isChecked ? 'ACTIVO' : 'INACTIVO';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast("ERROR DE CONEXIÓN");
            toggle.checked = !isChecked;
            statusText.textContent = !isChecked ? 'ACTIVO' : 'INACTIVO';
        });
}


/**
 * Abre el modal de confirmación para eliminar TODOS los certificados
 */
function confirmarEliminacionCertificados() {
    const modal = document.getElementById('deleteCertificatesModal');
    if (modal) modal.classList.remove('hidden');
}

/**
 * Cierra el modal de eliminación de certificados
 */
function closeDeleteCertificatesModal() {
    const modal = document.getElementById('deleteCertificatesModal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Ejecuta la eliminación masiva de certificados
 */
function confirmDeleteCertificates() {
    closeDeleteCertificatesModal();

    const formData = new FormData();
    formData.append('action', 'delete_certificates');
    formData.append('csrfmiddlewaretoken', csrftoken);

    // Mostrar loading overlay
    if (window.loadingOverlay) {
        window.loadingOverlay.show('Eliminando certificados y archivos físicos...');
    } else {
        showToast("ELIMINANDO CERTIFICADOS...");
    }

    fetch('', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(data.message.toUpperCase());

                if (window.loadingOverlay) {
                    window.loadingOverlay.updateMessage('¡Eliminación completada! Recargando...');
                }

                setTimeout(() => location.reload(), 1500);
            } else {
                showToast(data.error.toUpperCase());
                if (window.loadingOverlay) {
                    window.loadingOverlay.hide();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast("ERROR AL ELIMINAR");
            if (window.loadingOverlay) {
                window.loadingOverlay.hide();
            }
        });
}

/**
 * Abre el modal de eliminación de EVENTO completo
 */
function confirmarEliminacionEvento(eventoId, eventoNombre) {
    const modal = document.getElementById('deleteEventModal');
    const nameSpan = document.getElementById('eventoNombre');
    const form = document.getElementById('deleteEventForm');

    if (nameSpan) nameSpan.textContent = eventoNombre;
    if (form) form.action = `/certificados/evento/${eventoId}/eliminar/`;
    if (modal) modal.classList.remove('hidden');
}

/**
 * Cierra el modal de eliminación de evento
 */
function cerrarModalEvento() {
    const modal = document.getElementById('deleteEventModal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Maneja el estado visual de carga de la nómina
 * @param {boolean} isLoading - Si está cargando o no
 */
function setNominaLoading(isLoading) {
    const container = document.getElementById('estudiantesTableContainer');
    if (container) {
        if (isLoading) {
            container.classList.add('opacity-40', 'pointer-events-none', 'transition-opacity');
        } else {
            container.classList.remove('opacity-40', 'pointer-events-none');
        }
    }
}

/**
 * Actualiza la nómina de estudiantes mediante AJAX (Global)
 * @param {Object} params - Parámetros de búsqueda y orden
 */
function updateNomina(params) {
    const url = new URL(window.location.href);

    if (params.q !== undefined) {
        url.searchParams.set('q', params.q);
        url.searchParams.set('page', '1');
    }
    if (params.sort !== undefined) {
        url.searchParams.set('sort', params.sort);
    }

    setNominaLoading(true);

    fetch(url)
        .then(res => res.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newContainer = doc.getElementById('estudiantesTableContainer');
            const oldContainer = document.getElementById('estudiantesTableContainer');

            if (newContainer && oldContainer) {
                oldContainer.innerHTML = newContainer.innerHTML;
                window.history.pushState({}, '', url);
            }
        })
        .catch(err => {
            console.error('Error al actualizar nómina:', err);
            showToast("ERROR AL ACTUALIZAR LISTADO");
        })
        .finally(() => {
            setNominaLoading(false);
        });
}

/**
 * Aplica el ordenamiento global (A-Z / Z-A)
 * @param {string} direction - 'asc' o 'desc'
 */
function aplicarOrdenamiento(direction) {
    updateNomina({ sort: direction });
}

/**
 * Inicialización de listeners de eventos (CSP Compliant)
 */
document.addEventListener('DOMContentLoaded', function () {
    // Botones Principales
    const btnGenerate = document.getElementById('btnGenerate');
    if (btnGenerate) btnGenerate.addEventListener('click', startGeneration);

    const btnSend = document.getElementById('btnSend');
    if (btnSend) btnSend.addEventListener('click', openSendModal);

    const btnDeleteCertificates = document.getElementById('btnDeleteCertificates');
    if (btnDeleteCertificates) btnDeleteCertificates.addEventListener('click', confirmarEliminacionCertificados);

    const btnOpenCreateModal = document.getElementById('btnOpenCreateModal');
    if (btnOpenCreateModal) btnOpenCreateModal.addEventListener('click', openCreateModal);

    const toggleQrInput = document.getElementById('toggleQrInput');
    if (toggleQrInput) toggleQrInput.addEventListener('change', toggleQrSeguridad);

    const sortAsc = document.getElementById('sortAsc');
    if (sortAsc) sortAsc.addEventListener('click', () => aplicarOrdenamiento('asc'));

    const sortDesc = document.getElementById('sortDesc');
    if (sortDesc) sortDesc.addEventListener('click', () => aplicarOrdenamiento('desc'));

    // Búsqueda en nómina
    const nominaSearch = document.getElementById('nominaSearch');
    if (nominaSearch) {
        let searchTimeout;
        nominaSearch.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const val = e.target.value;
            if (val.length >= 5 || val.length === 0) {
                searchTimeout = setTimeout(() => updateNomina({ q: val }), 500);
            }
        });
    }

    // Delegación de eventos para la tabla de estudiantes
    const tableContainer = document.getElementById('estudiantesTableContainer');
    if (tableContainer) {
        tableContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-action]');
            if (!btn) return;

            const action = btn.dataset.action;
            const id = btn.dataset.id;

            if (action === 'generate-individual') {
                generateIndividual(id);
            } else if (action === 'edit-student') {
                openEditModal(id, btn.dataset.nombre, btn.dataset.correo);
            } else if (action === 'delete-student') {
                openDeleteModal(id, btn.dataset.nombre);
            }
        });
    }

    // Modal Listeners (Backdrops and Cancel Buttons)
    const modalMappings = [
        { id: 'editModal', cancel: 'btnCancelEdit', save: 'btnSaveEdit', backdrop: 'editModalBackdrop', closeFn: closeEditModal, saveFn: saveEditModal },
        { id: 'createModal', cancel: 'btnCancelCreate', save: 'btnSaveCreate', backdrop: 'createModalBackdrop', closeFn: closeCreateModal, saveFn: saveCreateModal },
        { id: 'deleteModal', cancel: 'btnCancelDelete', save: 'btnConfirmDelete', backdrop: 'deleteModalBackdrop', closeFn: closeDeleteModal, saveFn: confirmDeleteModal },
        { id: 'sendModal', cancel: 'btnCancelSend', save: 'btnConfirmSend', backdrop: 'sendModalBackdrop', closeFn: closeSendModal, saveFn: confirmSend },
        { id: 'deleteCertificatesModal', cancel: 'btnCancelDeleteCertificates', save: 'btnConfirmDeleteCertificates', backdrop: 'deleteCertificatesModalBackdrop', closeFn: closeDeleteCertificatesModal, saveFn: confirmDeleteCertificates },
        { id: 'deleteEventModal', cancel: 'btnCancelDeleteEvent', backdrop: 'deleteEventModalBackdrop', closeFn: cerrarModalEvento }
    ];

    modalMappings.forEach(m => {
        const cancelBtn = document.getElementById(m.cancel);
        if (cancelBtn) cancelBtn.addEventListener('click', m.closeFn);

        const saveBtn = document.getElementById(m.save);
        if (saveBtn) saveBtn.addEventListener('click', m.saveFn);

        const backdrop = document.getElementById(m.backdrop);
        if (backdrop) backdrop.addEventListener('click', m.closeFn);
    });
});
