/**
 * JavaScript para la gestión de usuarios (user_list.html)
 * Maneja modales de creación, edición, eliminación y estado toggle de usuarios
 */

// Alpine.js Data Object para el componente principal
const userListData = {
    showCreateModal: false,
    showEditModal: false,
    showDeleteModal: false,
    editUrl: '',
    deleteUrl: '',
    deleteName: '',
    loadingEdit: false,
    loadingCreate: false,

    openEditModal(url) {
        this.showEditModal = true;
        this.loadingEdit = true;
        this.editUrl = url;

        fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(response => response.text())
            .then(html => {
                document.getElementById('edit-form-outer').innerHTML = html;
                this.loadingEdit = false;
            })
            .catch(err => {
                console.error('Error loading form:', err);
                this.loadingEdit = false;
                Swal.fire('Error', 'Error al cargar el formulario.', 'error');
            });
    },

    submitCreateForm(event) {
        event.preventDefault();
        this.loadingCreate = true;
        const form = event.target;
        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return response.json();
                }
                return response.text();
            })
            .then(data => {
                if (typeof data === 'object' && data.success) {
                    window.location.href = data.redirect_url || window.location.href;
                } else if (typeof data === 'string') {
                    document.getElementById('create-form-container').innerHTML = data;
                    this.loadingCreate = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.loadingCreate = false;
                Swal.fire('Error', 'Error al procesar el formulario. Por favor, intente nuevamente.', 'error');
            });
    },

    submitEditForm(event) {
        event.preventDefault();
        this.loadingEdit = true;
        const form = event.target;
        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return response.json();
                }
                return response.text();
            })
            .then(data => {
                if (typeof data === 'object' && data.success) {
                    window.location.href = data.redirect_url || window.location.href;
                } else if (typeof data === 'string') {
                    document.getElementById('edit-form-outer').innerHTML = data;
                    this.loadingEdit = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.loadingEdit = false;
                Swal.fire('Error', 'Error al procesar el formulario. Por favor, intente nuevamente.', 'error');
            });
    }
};

// Funciones auxiliares
document.addEventListener('DOMContentLoaded', function () {
    /**
     * Verifica si la contraseña cumple los requisitos mínimos
     */
    function isPasswordStrong(val) {
        return val.length >= 10 && /[A-Z]/.test(val) && /[0-9]/.test(val);
    }

    /**
     * Maneja el envío de formularios con validación
     */
    function handleFormSubmit(form, modalVar) {
        const formData = new FormData(form);
        const url = form.action;

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return response.json();
                }
                return response.text();
            })
            .then(data => {
                if (typeof data === 'object' && data.success) {
                    window.location.href = data.redirect_url || window.location.href;
                } else if (typeof data === 'string') {
                    const container = form.closest('[id*="form"]');
                    if (container) {
                        container.innerHTML = data;
                    } else {
                        Swal.fire('Error', 'Error en el formulario. Por favor, revise los campos.', 'error');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Error', 'Error al procesar el formulario. Por favor, intente nuevamente.', 'error');
            });
    }

    // Validación para formulario de creación
    const createForm = document.querySelector('form[action*="create"]');
    if (createForm) {
        createForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const passwordField = this.querySelector('input[name="password1"]');
            if (passwordField && !isPasswordStrong(passwordField.value)) {
                Swal.fire('Contraseña Débil', 'La contraseña debe tener al menos 10 caracteres, una mayúscula y un número.', 'error');
                return;
            }
            handleFormSubmit(this, 'showCreateModal');
        });
    }

    // Validación para formulario de edición
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (form.matches('form[action*="edit"]') || form.matches('form[action*="update"]')) {
            e.preventDefault();
            const passwordField = form.querySelector('input[name="password1"]');
            if (passwordField && passwordField.value && !isPasswordStrong(passwordField.value)) {
                Swal.fire('Contraseña Débil', 'La contraseña debe tener al menos 10 caracteres, una mayúscula y un número.', 'error');
                return;
            }
            handleFormSubmit(form, 'showEditModal');
        }
    });
});
