function openConsultModal(cursoId, cursoNombre) {
    const modalCursoId = document.getElementById('modal-curso-id');
    const modalCursoName = document.getElementById('modal-curso-name');
    const consultModal = document.getElementById('consultModal');
    const cedulaInput = document.getElementById('cedula');

    if (modalCursoId) modalCursoId.value = cursoId;
    if (modalCursoName) modalCursoName.textContent = cursoNombre;
    if (consultModal) consultModal.classList.remove('hidden');
    if (cedulaInput) setTimeout(() => cedulaInput.focus(), 100);
}

function closeConsultModal() {
    const consultModal = document.getElementById('consultModal');
    if (consultModal) consultModal.classList.add('hidden');
}

// Cerrar con ESC
document.addEventListener('keydown', function (event) {
    if (event.key === "Escape") {
        closeConsultModal();
    }
});

// Expose functions to window
window.openConsultModal = openConsultModal;
window.closeConsultModal = closeConsultModal;
