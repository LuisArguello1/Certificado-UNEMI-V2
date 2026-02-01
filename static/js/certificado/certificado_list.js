/**
 * JavaScript para la lista de eventos/certificados
 * Maneja la confirmación y eliminación de eventos completos
 */

const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

function confirmarEliminacion(eventoId, eventoNombre) {
    document.getElementById('eventoNombre').textContent = eventoNombre;
    document.getElementById('deleteEventForm').action = `/certificados/evento/${eventoId}/eliminar/`;
    document.getElementById('deleteEventModal').classList.remove('hidden');
}

function cerrarModalEliminacion() {
    document.getElementById('deleteEventModal').classList.add('hidden');
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

    // Deshabilitar botón y mostrar loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> ELIMINANDO...';

    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Mostrar mensaje de éxito y redirigir
                cerrarModalEliminacion();
                if (window.Swal) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Eliminado',
                        text: data.message,
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.href = data.redirect_url || window.location.href;
                    });
                } else {
                    alert(data.message);
                    window.location.href = data.redirect_url || window.location.href;
                }
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            if (window.Swal) {
                Swal.fire('Error', error.message || 'No se pudo eliminar el evento.', 'error');
            } else {
                alert('Error: ' + (error.message || 'No se pudo eliminar el evento.'));
            }
        });
});
