/**
 * JavaScript para el formulario de generación de certificados.
 * Maneja Modales de Dirección y Plantilla, y drag & drop de Excel.
 */

document.addEventListener('DOMContentLoaded', function () {

    // =========================================================================
    // 1. MANEJO DE MODALES (DIRECCIÓN Y PLANTILLA)
    // =========================================================================

    // DOM Elements - Direccion
    const selectDireccionBtn = document.getElementById('selectDireccionBtn');
    const direccionModal = document.getElementById('direccionModal');
    const modalBackdrop = document.getElementById('modalBackdrop');
    const modalContent = document.getElementById('modalContent');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const direccionSearch = document.getElementById('direccionSearch');
    const direccionGrid = document.getElementById('direccionGrid');
    const hiddenDireccionInput = document.getElementById('id_direccion_gestion');
    const selectedDireccionText = document.getElementById('selectedDireccionText');

    // DOM Elements - Plantilla
    const plantillaModal = document.getElementById('plantillaModal');
    const plantillaBackdrop = document.getElementById('plantillaBackdrop');
    const plantillaContent = document.getElementById('plantillaContent');
    const closePlantillaModalBtn = document.getElementById('closePlantillaModalBtn');
    const plantillaListContainer = document.getElementById('plantillaListContainer');
    const selectedPlantillaText = document.getElementById('selectedPlantillaText');
    const hiddenPlantillaInput = document.getElementById('id_plantilla_seleccionada');
    const plantillaDisplayBox = document.getElementById('plantillaDisplayBox');
    const plantillaModalSubtitle = document.getElementById('plantillaModalSubtitle');

    // Estado local
    let currentDireccionId = null;
    let direcciones = [];

    // Cargar datos iniciales
    try {
        const dataScript = document.getElementById('direccionesData');
        if (dataScript) {
            direcciones = JSON.parse(dataScript.textContent);
        }
    } catch (e) {
        console.error('Error parseando direcciones:', e);
    }

    // Funciones Modal Dirección
    function openDireccionModal() {
        direccionModal.classList.remove('hidden');
        setTimeout(() => {
            modalBackdrop.classList.remove('opacity-0');
            modalContent.classList.remove('opacity-0', 'scale-95');
        }, 10);
        renderDirecciones(direcciones);
        direccionSearch.focus();
    }

    function closeDireccionModal() {
        modalBackdrop.classList.add('opacity-0');
        modalContent.classList.add('opacity-0', 'scale-95');
        setTimeout(() => {
            direccionModal.classList.add('hidden');
        }, 300);
    }

    function renderDirecciones(items) {
        direccionGrid.innerHTML = '';

        if (items.length === 0) {
            direccionGrid.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-search text-gray-200 text-3xl mb-3"></i>
                    <p class="text-gray-400 text-[10px] font-black uppercase tracking-widest">No se encontraron direcciones.</p>
                </div>
            `;
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-4';

        items.forEach(dir => {
            const card = document.createElement('div');
            card.className = 'flex items-center p-4 bg-white border border-gray-200 rounded-sm cursor-pointer hover:border-black hover:shadow-md transition-all group';
            card.addEventListener('click', () => selectDireccion(dir));

            card.innerHTML = `
                <div class="w-10 h-10 rounded-sm bg-gray-50 text-gray-400 flex items-center justify-center mr-4 group-hover:bg-black group-hover:text-white border border-gray-100 transition-colors">
                    <i class="fas fa-building text-sm"></i>
                </div>
                <div>
                    <h4 class="font-black text-gray-800 text-[10px] uppercase tracking-tighter">${dir.nombre}</h4>
                    <span class="inline-block mt-1 px-1.5 py-0.5 bg-gray-100 text-gray-500 text-[9px] rounded-sm font-bold uppercase tracking-widest group-hover:bg-gray-200">
                        ${dir.codigo}
                    </span>
                </div>
            `;
            grid.appendChild(card);
        });

        direccionGrid.appendChild(grid);
    }

    function selectDireccion(direccion) {
        currentDireccionId = direccion.id;
        selectedDireccionText.textContent = direccion.nombre.toUpperCase();
        selectedDireccionText.classList.remove('text-gray-400');
        selectedDireccionText.classList.add('text-black', 'font-black');
        hiddenDireccionInput.value = direccion.id;
        closeDireccionModal();
        setTimeout(() => {
            openPlantillaModal(direccion);
        }, 350);
    }

    // Funciones Modal Plantilla
    function openPlantillaModal(direccion) {
        plantillaModalSubtitle.textContent = `GESTIÓN: ${direccion.nombre.toUpperCase()}`;
        plantillaModal.classList.remove('hidden');
        plantillaListContainer.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-spinner fa-spin text-black text-2xl mb-4"></i>
                <p class="text-[9px] text-gray-400 font-black uppercase tracking-widest">Buscando diseños disponibles...</p>
            </div>
        `;
        setTimeout(() => {
            plantillaBackdrop.classList.remove('opacity-0');
            plantillaContent.classList.remove('opacity-0', 'scale-95');
        }, 10);

        fetch(`/certificados/api/plantillas/${direccion.id}/`)
            .then(response => response.json())
            .then(data => {
                renderPlantillas(data);
            })
            .catch(error => {
                console.error('Error:', error);
                plantillaListContainer.innerHTML = `
                    <div class="text-center py-8 text-red-500">
                        <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                        <p class="text-[10px] font-black uppercase tracking-widest">Error al cargar plantillas.</p>
                    </div>
                `;
            });
    }

    function closePlantillaModal() {
        plantillaBackdrop.classList.add('opacity-0');
        plantillaContent.classList.add('opacity-0', 'scale-95');
        setTimeout(() => {
            plantillaModal.classList.add('hidden');
        }, 300);
    }

    function renderPlantillas(data) {
        plantillaListContainer.innerHTML = '';
        if (!data.success || !data.plantilla_base) {
            plantillaListContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-12 text-center">
                    <div class="w-12 h-12 bg-gray-50 rounded-sm flex items-center justify-center mb-4 border border-gray-100">
                        <i class="fas fa-exclamation-triangle text-gray-300 text-xl"></i>
                    </div>
                    <h3 class="text-[10px] font-black text-gray-900 uppercase tracking-widest">Sin plantilla configurada</h3>
                    <p class="text-[9px] text-gray-400 mt-2 max-w-sm uppercase font-bold tracking-tighter">
                        Esta dirección no posee diseños base activos en el sistema.
                    </p>
                    <button type="button" id="closeNoPlantillasBtn" class="mt-6 px-5 py-2 bg-black text-white text-[9px] font-black uppercase tracking-widest rounded-sm hover:bg-gray-800">
                        CERRAR
                    </button>
                </div>
            `;
            const btn = document.getElementById('closeNoPlantillasBtn');
            if (btn) btn.addEventListener('click', closePlantillaModal);
            return;
        }

        const container = document.createElement('div');
        container.className = 'grid grid-cols-1 gap-4';

        const baseCard = createPlantillaCard({
            id: '',
            nombre: 'PLANTILLA BASE INSTITUCIONAL',
            descripcion: data.plantilla_base.descripcion || 'Diseño estándar oficial para certificaciones.',
            isBase: true
        });
        container.appendChild(baseCard);

        if (data.variantes && data.variantes.length > 0) {
            const separator = document.createElement('div');
            separator.className = 'flex items-center my-4';
            separator.innerHTML = `
                <div class="flex-grow border-t border-gray-100"></div>
                <span class="flex-shrink-0 mx-4 text-[9px] font-black text-gray-300 uppercase tracking-[0.3em]">Variantes</span>
                <div class="flex-grow border-t border-gray-100"></div>
            `;
            container.appendChild(separator);
            data.variantes.forEach(v => {
                container.appendChild(createPlantillaCard(v));
            });
        }
        plantillaListContainer.appendChild(container);
    }

    function createPlantillaCard(item) {
        const card = document.createElement('div');
        card.className = 'group relative flex items-start p-4 bg-white border border-gray-200 rounded-sm cursor-pointer hover:border-black transition-all';
        const isBase = item.isBase === true;
        const iconColor = 'text-gray-300 bg-gray-50 group-hover:bg-black group-hover:text-white border border-gray-100';
        const icon = isBase ? 'fa-certificate' : 'fa-layer-group';

        card.innerHTML = `
            <div class="flex-shrink-0 w-10 h-10 rounded-sm ${iconColor} flex items-center justify-center mr-4 transition-colors">
                <i class="fas ${icon} text-sm"></i>
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex justify-between items-start">
                    <h4 class="text-[10px] font-black text-gray-800 uppercase tracking-widest group-hover:text-black transition-colors">
                        ${item.nombre.toUpperCase()}
                    </h4>
                    ${isBase ? '<span class="px-2 py-0.5 rounded-sm text-[8px] font-black bg-black text-white tracking-tighter">BASE</span>' : ''}
                </div>
                <p class="text-[9px] text-gray-400 mt-1 line-clamp-2 uppercase font-bold tracking-tighter">${item.descripcion || 'Sin descripción'}</p>
            </div>
        `;
        card.addEventListener('click', () => selectPlantilla(item));
        return card;
    }

    function selectPlantilla(item) {
        hiddenPlantillaInput.value = item.id;
        selectedPlantillaText.textContent = item.nombre.toUpperCase();
        plantillaDisplayBox.classList.remove('opacity-60', 'bg-gray-50', 'border-dashed');
        plantillaDisplayBox.classList.add('bg-white', 'border-gray-300', 'text-black');
        const iconContainer = plantillaDisplayBox.querySelector('.w-8');
        if (iconContainer) {
            iconContainer.className = 'w-8 h-8 rounded-sm bg-black text-white flex items-center justify-center mr-3 border border-black';
        }
        closePlantillaModal();
    }

    if (selectDireccionBtn) selectDireccionBtn.addEventListener('click', openDireccionModal);
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeDireccionModal);
    if (closePlantillaModalBtn) closePlantillaModalBtn.addEventListener('click', closePlantillaModal);
    if (modalBackdrop) modalBackdrop.addEventListener('click', closeDireccionModal);

    if (direccionSearch) {
        direccionSearch.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = direcciones.filter(d =>
                d.nombre.toLowerCase().includes(term) ||
                d.codigo.toLowerCase().includes(term)
            );
            renderDirecciones(filtered);
        });
    }

    // =========================================================================
    // 2. EXCEL DRAG & DROP
    // =========================================================================

    const dropZone = document.getElementById('drop-zone-excel');
    const fileInput = document.querySelector('input[name="archivo_excel"]');
    const uploadPrompt = document.getElementById('upload-prompt');
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const removeFileBtn = document.getElementById('remove-file');

    if (dropZone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, e => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('border-black', 'bg-gray-50');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-black', 'bg-gray-50');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFiles(files);
            }
        });

        fileInput.addEventListener('change', function () {
            handleFiles(this.files);
        });

        // Nota: El clic ahora es manejado nativamente por el input transparente (z-10)
        // que cubre toda la zona.

        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                if (!file.name.match(/\.(xlsx|xls)$/)) {
                    alert('Solo se permiten archivos Excel (.xlsx, .xls)');
                    fileInput.value = '';
                    return;
                }
                updateFileUI(file);
            }
        }

        function updateFileUI(file) {
            fileName.textContent = file.name;
            fileSize.textContent = formatBytes(file.size);
            uploadPrompt.classList.add('hidden');
            filePreview.classList.remove('hidden');
        }

        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                fileInput.value = '';
                uploadPrompt.classList.remove('hidden');
                filePreview.classList.add('hidden');
            });
        }
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // =========================================================================
    // 3. SUBMIT LOGIC (SIMPLE DIRECT SUBMIT)
    // =========================================================================
    const form = document.getElementById('certificadoForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner');
    const btnIcon = document.getElementById('btnIcon');
    const btnText = document.getElementById('btnText');

    if (form) {
        form.addEventListener('submit', function (e) {
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            if (!fileInput.files.length) {
                e.preventDefault();
                alert('Por favor carga un archivo Excel.');
                return;
            }

            // Show loading
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-75', 'cursor-wait');
            if (spinner) spinner.style.display = 'inline-block';
            if (btnIcon) btnIcon.style.display = 'none';
            btnText.textContent = 'CREANDO EVENTO...';
        });
    }
});
