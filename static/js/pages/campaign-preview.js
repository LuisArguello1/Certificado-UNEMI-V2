// --- Lógica Modal Destinatarios con Paginación ---
let allRecipients = [];
const ITEMS_PER_PAGE = 20;
let currentPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    try {
        const dataElement = document.getElementById('recipients-data');
        if (dataElement) {
            allRecipients = JSON.parse(dataElement.textContent);
        }
    } catch (e) { console.error("Error parsing recipients json", e); }
});

function openRecipientsModal() {
    const modal = document.getElementById('recipientsModal');
    if (modal) {
        modal.classList.remove('hidden');
        renderTable(1);
    }
}

function closeRecipientsModal() {
    const modal = document.getElementById('recipientsModal');
    if (modal) modal.classList.add('hidden');
}

function renderTable(page) {
    currentPage = page;
    const tbody = document.getElementById('modal-recipients-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    const start = (page - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageItems = allRecipients.slice(start, end);

    pageItems.forEach((r, index) => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-gray-50";
        tr.innerHTML = `
            <td class="px-6 py-3 whitespace-nowrap text-gray-400 text-xs">${start + index + 1}</td>
            <td class="px-6 py-3 whitespace-nowrap font-medium text-gray-900">${r.full_name}</td>
            <td class="px-6 py-3 whitespace-nowrap text-gray-500">${r.email}</td>
        `;
        tbody.appendChild(tr);
    });

    // Controles paginación
    const totalPages = Math.ceil(allRecipients.length / ITEMS_PER_PAGE);
    const info = document.getElementById('pageInfo');
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');

    if (info) info.innerText = `Página ${currentPage} de ${totalPages}`;
    if (btnPrev) btnPrev.disabled = currentPage === 1;
    if (btnNext) btnNext.disabled = currentPage >= totalPages;
}

function prevPage() {
    if (currentPage > 1) renderTable(currentPage - 1);
}

function nextPage() {
    const totalPages = Math.ceil(allRecipients.length / ITEMS_PER_PAGE);
    if (currentPage < totalPages) renderTable(currentPage + 1);
}

// --- Lógica Modal Confirmación ---
function openConfirmModal() {
    const modal = document.getElementById('confirmModal');
    if (modal) modal.classList.remove('hidden');
}

function closeConfirmModal() {
    const modal = document.getElementById('confirmModal');
    if (modal) modal.classList.add('hidden');
}

// --- Loading State ---
function handleSendSubmit() {
    const btn = document.getElementById('btnConfirmSend');

    // Desactivar botón y cambiar texto
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Procesando envío...';
        btn.classList.add('opacity-75', 'cursor-not-allowed');
    }

    // El formulario se enviará normalmente después de esto
    return true;
}

// Exponer funciones al window para que los eventos onclick del HTML funcionen
window.openRecipientsModal = openRecipientsModal;
window.closeRecipientsModal = closeRecipientsModal;
window.prevPage = prevPage;
window.nextPage = nextPage;
window.openConfirmModal = openConfirmModal;
window.closeConfirmModal = closeConfirmModal;
window.handleSendSubmit = handleSendSubmit;
