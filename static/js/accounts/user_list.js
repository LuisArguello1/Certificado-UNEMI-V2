/**
 * JavaScript para la gestión de usuarios (user_list.html)
 * Maneja modales de creación, edición, eliminación y cambio de contraseña
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('userListData', () => ({
        showCreateModal: false,
        showEditModal: false,
        showDeleteModal: false,

        editUrl: '',
        deleteUrl: '',
        deleteName: '',

        loadingEdit: false,
        loadingCreate: false,

        // Cambio de contraseña
        showPasswordModal: false,
        loadingPassword: false,
        passwordUrl: '',
        passwordChangeName: '',

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
                    Swal.fire('Error', 'Error al procesar el formulario.', 'error');
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
                    Swal.fire('Error', 'Error al procesar el formulario.', 'error');
                });
        },

        openPasswordModal(url, username) {
            this.showPasswordModal = true;
            this.loadingPassword = true;
            this.passwordUrl = url;
            this.passwordChangeName = username;

            fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(response => response.text())
                .then(html => {
                    document.getElementById('password-form-container').innerHTML = html;
                    this.loadingPassword = false;
                })
                .catch(err => {
                    console.error('Error loading password form:', err);
                    this.loadingPassword = false;
                    Swal.fire('Error', 'Error al cargar el formulario de contraseña.', 'error');
                });
        },

        submitPasswordForm(event) {
            event.preventDefault();
            this.loadingPassword = true;
            const form = event.target;
            const formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.showPasswordModal = false;
                        Swal.fire('Éxito', data.message, 'success');
                    } else {
                        let errorMsg = 'Error al cambiar la contraseña.';
                        if (data.errors) {
                            const firstKey = Object.keys(data.errors)[0];
                            errorMsg = data.errors[firstKey][0].message || errorMsg;
                        }
                        Swal.fire('Validación', errorMsg, 'warning');
                    }
                    this.loadingPassword = false;
                })
                .catch(error => {
                    console.error('Error:', error);
                    this.loadingPassword = false;
                    Swal.fire('Error', 'Error técnico al procesar el cambio.', 'error');
                });
        }
    }));
});

// Funciones auxiliares para validación inmediata si se requiere
document.addEventListener('DOMContentLoaded', function () {
    function isPasswordStrong(val) {
        return val.length >= 10 && /[A-Z]/.test(val) && /[0-9]/.test(val);
    }

    // Nota: El manejo de submit ahora está centralizado en el objeto Alpine
    // Pero si hay formularios que no usan Alpine directamente, se mantienen estos listeners
});
