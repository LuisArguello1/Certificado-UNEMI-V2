/**
 * JavaScript para la lista de eventos/certificados
 * Maneja la confirmación y eliminación de eventos completos
 */

// Función para obtener el token CSRF
function getCSRFToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}

function confirmarEliminacion(eventoId, eventoNombre) {
    const nameEl = document.getElementById('eventoNombre');
    const formEl = document.getElementById('deleteEventForm');
    const modalEl = document.getElementById('deleteEventModal');

    if (nameEl) nameEl.textContent = eventoNombre;
    if (formEl) formEl.action = `/certificados/evento/${eventoId}/eliminar/`;
    if (modalEl) modalEl.classList.remove('hidden');
}

function cerrarModalEliminacion() {
    const modalEl = document.getElementById('deleteEventModal');
    if (modalEl) modalEl.classList.add('hidden');
}

// Cerrar modal al hacer clic fuera
document.getElementById('deleteEventModal')?.addEventListener('click', function (e) {
    if (e.target === this) {
        cerrarModalEliminacion();
    }
});

// Manejar envío del formulario
document.getElementById('deleteEventForm')?.addEventListener('submit', function (e) {
    e.preventDefault();

    const form = this;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    const token = getCSRFToken();

    // Deshabilitar botón y mostrar loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> ELIMINANDO...';

    // Para eliminación simple, es mejor NO enviar JSON si la vista espera POST normal
    // O simplemente usar FormData
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': token,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new FormData(form)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cerrarModalEliminacion();
                if (window.Swal) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Eliminado',
                        text: data.message,
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    alert(data.message);
                    window.location.reload();
                }
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            console.error('Error en proceso de eliminación:', error);
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            if (window.Swal) {
                Swal.fire('Error', error.message || 'No se pudo eliminar el evento.', 'error');
            } else {
                alert('Error: ' + (error.message || 'No se pudo eliminar el evento.'));
            }
        });
});// Inicialización (CSP Compliant)
document.addEventListener('DOMContentLoaded', function () {
    // Delegación de eventos para la tabla
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('button[data-action="delete-event"]');
        if (btn) {
            confirmarEliminacion(btn.dataset.id, btn.dataset.nombre);
        }
    });

    // Botón cancelar modal
    const btnCancel = document.getElementById('btnCancelDelete');
    if (btnCancel) {
        btnCancel.addEventListener('click', cerrarModalEliminacion);
    }

    // Buscador con auto-submit
    const searchInput = document.querySelector('input[name="search"]');
    const searchForm = searchInput?.closest('form');

    if (searchInput && searchForm) {
        let searchTimeout;
        searchInput.addEventListener('input', function (e) {
            clearTimeout(searchTimeout);
            const value = e.target.value.trim();

            // Auto-submit después de 500ms de inactividad
            // O inmediatamente si se vacía el campo
            if (value.length >= 3 || value.length === 0) {
                searchTimeout = setTimeout(() => {
                    searchForm.submit();
                }, value.length === 0 ? 0 : 500);
            }
        });
    }
});

