/**
 * JavaScript para gestión de formulario de plantillas con formset dinámico
 * 
 * Funcionalidades:
 * - Drag & drop para archivo base
 * - Agregar/eliminar variantes dinámicamente
 * - Validación de archivos .docx
 * - Loading state en submit
 */

document.addEventListener('DOMContentLoaded', function () {

    // =========================================================================
    // DRAG & DROP PARA ARCHIVO BASE
    // =========================================================================

    const dropZoneBase = document.getElementById('drop-zone-base');
    const fileInputBase = document.getElementById('id_archivo_base');
    const promptBase = document.getElementById('upload-prompt-base');
    const previewBase = document.getElementById('file-preview-base');
    const fileNameBase = document.getElementById('file-name-base');

    if (dropZoneBase && fileInputBase) {
        // Prevenir comportamiento por defecto
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZoneBase.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Highlight en drag over
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZoneBase.addEventListener(eventName, () => {
                dropZoneBase.classList.add('border-indigo-500', 'bg-indigo-50');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZoneBase.addEventListener(eventName, () => {
                dropZoneBase.classList.remove('border-indigo-500', 'bg-indigo-50');
            }, false);
        });

        // Handle drop
        dropZoneBase.addEventListener('drop', function (e) {
            const files = e.dataTransfer.files;
            handleBaseFile(files);
        }, false);

        // Handle file input change
        fileInputBase.addEventListener('change', function () {
            handleBaseFile(this.files);
        });

        function handleBaseFile(files) {
            if (files.length > 0) {
                const file = files[0];

                // Validar extensión
                if (!file.name.toLowerCase().endsWith('.docx')) {
                    alert('Solo se permiten archivos con extensión .docx');
                    fileInputBase.value = '';
                    return;
                }

                // Validar tamaño (10MB)
                if (file.size > 10 * 1024 * 1024) {
                    alert('El archivo no debe superar los 10MB');
                    fileInputBase.value = '';
                    return;
                }

                // Actualizar UI
                promptBase.classList.add('hidden');
                previewBase.classList.remove('hidden');
                fileNameBase.textContent = file.name;
            }
        }
    }

    // =========================================================================
    // FORMSET DINÁMICO PARA VARIANTES
    // =========================================================================

    const addVarianteBtn = document.getElementById('add-variante');
    const variantesContainer = document.getElementById('variantes-container');
    const totalFormsInput = document.querySelector('#id_variantes-TOTAL_FORMS');

    if (addVarianteBtn && variantesContainer && totalFormsInput) {

        // Contador de formularios
        let formIdx = parseInt(totalFormsInput.value);

        // Template base para nuevo formulario
        const emptyFormTemplate = `
            <div class="variante-form-item bg-gradient-to-r from-gray-50 to-blue-50/30 border border-gray-200 rounded-lg p-4 mb-4 relative">
                <button type="button" class="remove-variante absolute top-2 right-2 inline-flex items-center px-2 py-1 text-xs text-red-600 cursor-pointer hover:bg-red-50 rounded-sm transition-colors font-bold">
                    <i class="fas fa-trash mr-1"></i> Eliminar
                </button>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <!-- Nombre -->
                    <div>
                        <label class="block text-xs font-bold text-gray-700 mb-1">Nombre *</label>
                        <input type="text" name="variantes-__prefix__-nombre" 
                               class="w-full px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500" 
                               placeholder="Ej: Con Logo Grande">
                    </div>

                    <!-- Orden -->
                    <div>
                        <label class="block text-xs font-bold text-gray-700 mb-1">Orden</label>
                        <input type="number" name="variantes-__prefix__-orden" value="0" min="0"
                               class="w-full px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500">
                    </div>

                    <!-- Activo -->
                    <div class="flex items-center pt-5">
                        <input type="checkbox" name="variantes-__prefix__-activo" checked
                               class="rounded text-indigo-600 focus:ring-indigo-500">
                        <label class="ml-2 block text-xs text-gray-700 font-bold">Activa</label>
                    </div>

                    <!-- Archivo -->
                    <div class="md:col-span-3">
                        <label class="block text-xs font-bold text-gray-700 mb-1">Archivo .docx *</label>
                        <input type="file" name="variantes-__prefix__-archivo" accept=".docx"
                               class="block w-full text-xs text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-sm file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition-colors">
                    </div>

                    <!-- Descripción -->
                    <div class="md:col-span-3">
                        <label class="block text-xs font-bold text-gray-700 mb-1">Descripción</label>
                        <textarea name="variantes-__prefix__-descripcion" rows="2"
                                  class="w-full px-3 py-1.5 text-xs border border-gray-300 rounded-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                  placeholder="Descripción opcional..."></textarea>
                    </div>
                </div>

                <input type="hidden" name="variantes-__prefix__-id">
            </div>
        `;


        // Agregar nueva variante
        addVarianteBtn.addEventListener('click', function () {
            // Reemplazar __prefix__ con el índice actual
            const newForm = emptyFormTemplate.replace(/__prefix__/g, formIdx);

            // Insertar antes del template vacío
            variantesContainer.insertAdjacentHTML('beforeend', newForm);

            // Incrementar contador
            formIdx++;
            totalFormsInput.value = formIdx;

            // Agregar event listener al botón de eliminar
            attachRemoveListeners();
        });

        // Eliminar variante
        function attachRemoveListeners() {
            const removeButtons = document.querySelectorAll('.remove-variante');
            removeButtons.forEach(btn => {
                btn.addEventListener('click', function () {
                    const formItem = this.closest('.variante-form-item');

                    // Verificar si tiene checkbox DELETE (formulario existente)
                    const deleteCheckbox = formItem.querySelector('input[name$="-DELETE"]');
                    if (deleteCheckbox) {
                        // Marcar para eliminación
                        deleteCheckbox.checked = true;
                        formItem.style.display = 'none';
                    } else {
                        // Eliminar del DOM (formulario nuevo)
                        formItem.remove();
                        // Decrementar contador
                        formIdx--;
                        totalFormsInput.value = formIdx;
                    }
                });
            });
        }

        // Inicializar listeners para formularios existentes
        attachRemoveListeners();
    }

    // =========================================================================
    // SUBMIT CON LOADING STATE
    // =========================================================================

    const plantillaForm = document.getElementById('plantillaForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btnText');

    if (plantillaForm && submitBtn) {
        plantillaForm.addEventListener('submit', function (e) {
            // Validar antes de mostrar loading
            if (!plantillaForm.checkValidity()) {
                return; // Dejar que el navegador muestre errores de validación
            }

            // Mostrar loading state
            submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
            submitBtn.disabled = true;
            spinner.classList.remove('hidden');
            btnText.textContent = 'Guardando...';
        });
    }

    // =========================================================================
    // VALIDACIÓN DE ARCHIVOS .DOCX EN VARIANTES
    // =========================================================================

    // Delegar evento para archivos de variantes (actuales y futuros)
    variantesContainer?.addEventListener('change', function (e) {
        if (e.target.type === 'file' && e.target.name.includes('archivo')) {
            const file = e.target.files[0];

            if (file) {
                // Validar extensión
                if (!file.name.toLowerCase().endsWith('.docx')) {
                    alert('Solo se permiten archivos con extensión .docx');
                    e.target.value = '';
                    return;
                }

                // Validar tamaño
                if (file.size > 10 * 1024 * 1024) {
                    alert('El archivo no debe superar los 10MB');
                    e.target.value = '';
                    return;
                }
            }
        }
    });
});

// =========================================================================
// MODAL SELECTOR DE DIRECCIONES
// =========================================================================

document.addEventListener('DOMContentLoaded', function () {
    const selectBtn = document.getElementById('selectDireccionBtn');
    const modal = document.getElementById('direccionModal');
    const closeBtn = document.getElementById('closeDireccionModal');
    const direccionesGrid = document.getElementById('direccionesGrid');
    const hiddenInput = document.getElementById('id_direccion');
    const displayDiv = document.getElementById('selectedDireccionDisplay');

    if (!selectBtn || !modal) return;

    // Abrir modal
    selectBtn.addEventListener('click', function () {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        cargarDirecciones();
    });

    // Cerrar modal
    closeBtn?.addEventListener('click', function () {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    });

    // Cerrar al hacer click fuera
    modal.addEventListener('click', function (e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    });

    // Cargar direcciones desde el dataset del select button
    function cargarDirecciones() {
        // Obtener direcciones desde atributo data del botón o global
        const direccionesData = window.DIRECCIONES_DATA || [];

        if (direccionesData.length === 0) {
            direccionesGrid.innerHTML = '<p class="text-center text-gray-500 text-sm py-8">No hay direcciones disponibles.</p>';
            return;
        }

        direccionesGrid.innerHTML = `
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                ${direccionesData.map(dir => `
                    <button type="button" class="direccion-card text-left p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-all ${!dir.activo ? 'opacity-50' : ''}" data-id="${dir.id}" data-nombre="${dir.nombre}" data-codigo="${dir.codigo}">
                        <div class="flex items-start">
                            <div class="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center mr-3">
                                <i class="fas fa-folder text-indigo-600 text-xl"></i>
                            </div>
                            <div class="flex-1 min-w-0">
                                <h3 class="text-sm font-bold text-gray-900 truncate">${dir.nombre}</h3>
                                <p class="text-xs text-gray-500 mt-0.5">Código: ${dir.codigo}</p>
                                ${!dir.activo ? '<span class="inline-block mt-1 text-[9px] bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full font-bold">INACTIVA</span>' : '<span class="inline-block mt-1 text-[9px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">ACTIVA</span>'}
                            </div>
                        </div>
                    </button>
                `).join('')}
            </div>
        `;

        // Event listeners para cada card
        document.querySelectorAll('.direccion-card').forEach(card => {
            card.addEventListener('click', function () {
                const id = this.dataset.id;
                const nombre = this.dataset.nombre;
                const codigo = this.dataset.codigo;

                // Actualizar input hidden
                hiddenInput.value = id;

                // Actualizar display
                displayDiv.innerHTML = `
                    <i class="fas fa-folder text-indigo-600 mr-3 text-xl"></i>
                    <div>
                        <span class="block text-sm font-bold text-gray-900">${nombre}</span>
                        <span class="text-xs text-gray-500">Código: ${codigo}</span>
                    </div>
                `;

                // Cerrar modal
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            });
        });
    }
});

