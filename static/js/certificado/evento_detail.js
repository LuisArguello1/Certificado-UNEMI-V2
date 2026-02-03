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
        const icon = btn.querySelector('i');
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

// Inicialización al cargar la página
document.addEventListener('DOMContentLoaded', function () {
    // Si hay un lote en proceso, iniciar polling automáticamente
    const progressSection = document.getElementById('progressSection');
    if (progressSection && !progressSection.classList.contains('hidden')) {
        startPolling();
    }
});
