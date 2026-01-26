// ==========================================
// EDITOR DE CERTIFICADOS - ARQUITECTURA MODULAR
// ==========================================

// === CONFIGURACIÓN ===
const DEFAULTS = {
    textbox: { x_pct: 35, y_pct: 45, width_pct: 30, fontSize: 24, color: '#000000', text: 'Nuevo texto', fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    image: { x_pct: 40, y_pct: 40, width_pct: 20, height_pct: 15, fontSize: 0, color: 'transparent', text: '', src: '', fontFamily: 'Arial', textAlign: 'center', rotation: 0 },
    title: { x_pct: 20, y_pct: 10, width_pct: 60, fontSize: 48, color: '#2E7D32', text: 'CERTIFICADO DE PARTICIPACIÓN', bold: true, fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    subtitle: { x_pct: 25, y_pct: 20, width_pct: 50, fontSize: 20, color: '#666666', text: 'Por medio de la presente se certifica que:', fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    student: { x_pct: 30, y_pct: 30, width_pct: 40, fontSize: 42, color: '#2E7D32', text: 'JUAN CARLOS PEREZ LOPEZ', bold: true, fontFamily: 'Arial, sans-serif', textAlign: 'center', originalText: 'JUAN CARLOS PEREZ LOPEZ', rotation: 0 },
    course_intro: { x_pct: 30, y_pct: 42, width_pct: 40, fontSize: 18, color: '#666666', text: 'ha participado en el curso:', fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    course: { x_pct: 25, y_pct: 48, width_pct: 50, fontSize: 32, color: '#1a237e', text: 'Gestión de Proyectos', bold: true, fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    dates: { x_pct: 20, y_pct: 58, width_pct: 60, fontSize: 18, color: '#666666', text: 'con una duración desde 01/03/2024 hasta 30/06/2024', fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    responsible: { x_pct: 25, y_pct: 65, width_pct: 50, fontSize: 18, color: '#666666', text: 'bajo la responsabilidad de M. Rodriguez', fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    signature: { x_pct: 15, y_pct: 78, width_pct: 25, fontSize: 14, color: '#333333', text: '_____________________\n\nFirma del Responsable', fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    footer: { x_pct: 15, y_pct: 90, width_pct: 70, fontSize: 12, color: '#888888', text: 'En constancia se expide el presente certificado', fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    cedula: { x_pct: 30, y_pct: 35, width_pct: 40, fontSize: 16, color: '#666666', text: 'C.I. 1234567890', fontFamily: 'Arial, sans-serif', textAlign: 'center', rotation: 0 },
    issue_date: { x_pct: 70, y_pct: 85, width_pct: 25, fontSize: 14, color: '#000000', text: 'Emitido el: 30 de junio de 2024', fontFamily: 'Arial, sans-serif', textAlign: 'right', rotation: 0 }
};

const PLACEHOLDERS = {
    textbox: 'Nuevo texto', student: '[NOMBRE DEL ESTUDIANTE]', course: '[NOMBRE DEL CURSO]',
    responsible: 'bajo la responsabilidad de [RESPONSABLE]', dates: 'con una duración desde [FECHA_INICIO] hasta [FECHA_FIN]',
    signature: '_____________________\n\n[TIPO DE FIRMA]', footer: 'En constancia se expide el presente certificado',
    title: 'CERTIFICADO DE PARTICIPACIÓN', subtitle: 'Por medio de la presente se certifica que:',
    course_intro: 'ha participado en el curso:', cedula: 'C.I. [CEDULA]', issue_date: 'Emitido el: [FECHA_EMISION]'
};

// === ESTADO GLOBAL ===
let blocks = [];
let selectedId = null;
let zoom = 0.75;
let naturalW = 100; // Temporal
let naturalH = 100;

const canvas = document.getElementById('certificate-area');
const container = document.getElementById('canvasContainer');
const bg = document.getElementById('certificate-bg');

document.addEventListener('DOMContentLoaded', () => {
    if (bg.complete) { initEditor(); } else { bg.onload = initEditor; }
});

function initEditor() {
    if (!bg.naturalWidth || bg.naturalWidth < 100) {
        console.warn('Esperando resolución de imagen...');
        setTimeout(initEditor, 100); return;
    }
    naturalW = bg.naturalWidth;
    naturalH = bg.naturalHeight;
    canvas.style.width = `${naturalW}px`;
    canvas.style.height = `${naturalH}px`;

    const titleEl = document.querySelector('.toolbar-title');
    if (titleEl && !document.getElementById('res-info')) {
        const info = document.createElement('span');
        info.id = 'res-info';
        info.style.cssText = 'font-size:11px; opacity:0.8; margin-left:15px; color:#fff; border-left:1px solid rgba(255,255,255,0.3); padding-left:15px;';
        info.innerText = `Lienzo Base: ${naturalW}x${naturalH}px`;
        titleEl.appendChild(info);
    }

    if (!document.getElementById('snap-v')) {
        const sv = document.createElement('div'); sv.id = 'snap-v'; sv.className = 'snap-line-v'; canvas.appendChild(sv);
        const sh = document.createElement('div'); sh.id = 'snap-h'; sh.className = 'snap-line-h'; canvas.appendChild(sh);
    }

    loadSavedConfig();
    setupEventListeners();
    setTimeout(() => { fitToWindow(); render(); }, 100);
}

function loadSavedConfig() {
    // Intentar cargar desde el script tag seguro (Django json_script)
    const scriptTag = document.getElementById('config-data');
    let configData = null;

    if (scriptTag) {
        try {
            configData = JSON.parse(scriptTag.textContent);
            // CRITICAL FIX: Si configData es un string (doble serialización), parsearlo de nuevo.
            if (typeof configData === 'string') {
                try {
                    configData = JSON.parse(configData);
                } catch (e) {
                    console.error('Error parsing inner JSON string:', e);
                    configData = null;
                }
            }
        } catch (e) { console.error('Error parsing config from script tag:', e); }
    }

    // Fallback al input hidden si no hay script tag (compatibilidad)
    if (!configData) {
        const saved = document.getElementById('savedConfig')?.value || '';
        if (saved && saved !== 'None' && saved !== '{}' && saved !== '') {
            try {
                configData = JSON.parse(saved);
            } catch (e) { console.error('Error parsing config from input:', e, saved); }
        }
    }

    if (configData && typeof configData === 'object') {
        blocks = Object.keys(configData).map(id => {
            const b = configData[id];
            if (typeof b !== 'object') return null; // Skip invalid entries

            let x_pct, y_pct;
            const img_w = b.image_w || naturalW;
            const img_h = b.image_h || naturalH;
            if (b.x_px !== undefined && b.y_px !== undefined) {
                x_pct = (b.x_px / img_w) * 100;
                y_pct = (b.y_px / img_h) * 100;
            } else { x_pct = b.x_pct || b.x || 50; y_pct = b.y_pct || b.y || 50; }

            // Ensure font family quotes are handled cleanly
            let fontFamily = b.fontFamily || b.font_family || 'Arial, sans-serif';
            // If it came with escaped quotes from previous bad saves, clean them? 
            // Usually JSON.parse handles the string correctly.

            return {
                id, type: b.type || 'textbox', x_pct, y_pct,
                width_pct: b.width_pct || (b.width_px ? (b.width_px / img_w * 100) : 30),
                height_pct: b.height_pct || (b.height_px ? (b.height_px / img_h * 100) : undefined),
                src: b.src || (b.type === 'image' ? b.text_override : '') || '',
                fontSize: b.font_size || b.fontSize || 24,
                color: b.color || '#000000', text: b.text_override || b.text || 'Texto',
                bold: !!b.bold, italic: !!b.italic, underline: !!b.underline,
                fontFamily: fontFamily,
                textAlign: b.textAlign || b.text_align || 'center',
                letterSpacing: b.letterSpacing || b.letter_spacing || 0,
                rotation: b.rotation || 0, opacity: b.opacity !== undefined ? b.opacity : 1,
                nameFormat: b.name_format || 'full'
            };
        });
        render(); // Force render after loading
    }
}

function setupEventListeners() {
    // Dropdown helpers
    window.closeDropdown = function () { document.getElementById('dropdown')?.classList.remove('show'); };
    window.toggleDropdown = function (e) { if (e) e.stopPropagation(); document.getElementById('dropdown')?.classList.toggle('show'); };

    document.addEventListener('click', (e) => { if (!e.target.closest('.dropdown')) closeDropdown(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Delete' && selectedId) { deleteBlockDirect(); } });

    const inputs = ['text', 'fontFamily', 'fontSize', 'color', 'letterSpacing', 'opacity', 'rotation', 'widthPct', 'heightPct'];
    inputs.forEach(id => {
        document.getElementById(id)?.addEventListener('input', (e) => {
            if (!selectedId) return;
            const b = blocks.find(b => b.id === selectedId);
            const v = e.target.value;
            if (id === 'text') b.text = v;
            if (id === 'fontFamily') b.fontFamily = v;
            if (id === 'fontSize') { b.fontSize = parseInt(v); document.getElementById('fontSizeVal').innerText = v + 'px'; }
            if (id === 'color') b.color = v;
            if (id === 'letterSpacing') { b.letterSpacing = parseFloat(v); document.getElementById('letterSpacingVal').innerText = v + 'px'; }
            if (id === 'opacity') { b.opacity = parseFloat(v); document.getElementById('opacityVal').innerText = Math.round(v * 100) + '%'; }
            if (id === 'rotation') { b.rotation = parseInt(v); document.getElementById('rotationVal').innerText = v + '°'; }
            if (id === 'widthPct') b.width_pct = parseFloat(v);
            if (id === 'heightPct') b.height_pct = parseFloat(v);
            updateElement(selectedId);
        });
    });

    document.getElementById('nameFormat')?.addEventListener('change', (e) => {
        if (!selectedId) return;
        const b = blocks.find(b => b.id === selectedId);
        if (b.type === 'student') {
            b.nameFormat = e.target.value;
            if (!b.originalText || b.originalText.includes('[NOMBRE')) b.originalText = 'JUAN CARLOS PEREZ LOPEZ';
            const parts = b.originalText.split(' '), mode = e.target.value;
            let f = b.originalText;
            if (parts.length > 0) {
                const fir = parts[0], las = parts.length > 1 ? parts[parts.length - 1] : '';
                if (mode === 'first_last') f = `${fir} ${las}`.trim();
                else if (mode === 'f_last') f = `${fir[0]}. ${las}`.trim();
                else if (mode === 'first_l') f = las ? `${fir} ${las[0]}.` : fir;
                else if (mode === 'fl') f = las ? `${fir[0]}. ${las[0]}.` : `${fir[0]}.`;
            }
            b.text = f; if (document.getElementById('text')) document.getElementById('text').value = f;
            updateElement(selectedId);
        }
    });
}

window.uploadImage = function (input) {
    if (input.files && input.files[0]) {
        const fd = new FormData(); fd.append('image', input.files[0]);
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        fetch(UPLOAD_URL, { method: 'POST', body: fd, headers: { 'X-CSRFToken': csrftoken } })
            .then(r => r.json()).then(data => {
                if (data.url && selectedId) {
                    const b = blocks.find(b => b.id === selectedId);
                    b.src = data.url; b.text = data.url; b.width_pct = b.width_pct || 20;
                    render(); select(selectedId);
                }
            });
    }
}

function switchTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.getElementById('tab-' + name)?.classList.add('active');
    document.querySelectorAll('.tab').forEach(t => { if (t.getAttribute('onclick')?.includes(`'${name}'`)) t.classList.add('active'); });
}

function toggleGrid() {
    const g = document.getElementById('grid-overlay');
    if (g) {
        g.classList.toggle('show');
        const btn = document.getElementById('btnGrid');
        if (btn) btn.classList.toggle('active');
    }
}

function setZoom(z, btn) { zoom = z; if (container) container.style.transform = `scale(${z})`; document.querySelectorAll('.zoom-btn').forEach(b => b.classList.remove('active')); if (btn) btn.classList.add('active'); }

function fitToWindow() {
    const ws = document.getElementById('workspace'); if (!ws || !bg) return;
    const sX = (ws.clientWidth - 40) / naturalW, sY = (ws.clientHeight - 40) / naturalH;
    zoom = Math.min(sX, sY, 1); if (container) container.style.transform = `scale(${zoom})`;
}

function addBlock(type) {
    const id = 'block_' + Date.now();
    let def = DEFAULTS[type] || DEFAULTS['textbox'];
    blocks.push({
        id, type, x_pct: def.x_pct, y_pct: def.y_pct, width_pct: def.width_pct || 30, height_pct: def.height_pct,
        fontSize: def.fontSize, color: def.color, text: def.text, src: def.src || '',
        bold: !!def.bold, italic: !!def.italic, underline: false, fontFamily: def.fontFamily || 'Arial, sans-serif',
        textAlign: def.textAlign || 'center', rotation: def.rotation || 0, letterSpacing: 0, opacity: 1, nameFormat: 'full'
    });
    render(); select(id); switchTab('props');
}

function render() {
    if (!canvas) return;
    canvas.querySelectorAll('.draggable-element').forEach(el => el.remove());
    const list = document.getElementById('blocks-list'); if (list) list.innerHTML = '';
    if (blocks.length === 0) { if (document.getElementById('empty-elements')) document.getElementById('empty-elements').style.display = 'block'; return; }
    if (document.getElementById('empty-elements')) document.getElementById('empty-elements').style.display = 'none';

    blocks.forEach(b => {
        const el = document.createElement('div');
        el.id = b.id; el.className = 'draggable-element' + (selectedId === b.id ? ' selected' : '');
        el.style.cssText = `position:absolute; left:${b.x_pct}%; top:${b.y_pct}%; width:${b.width_pct}%; 
                           ${b.height_pct ? `height:${b.height_pct}%;` : ''} transform:rotate(${b.rotation}deg); 
                           opacity:${b.opacity}; box-sizing:border-box; line-height:1; padding:0;`;
        el.onclick = (e) => { e.stopPropagation(); select(b.id); };

        if (b.type === 'image') {
            const img = document.createElement('img');
            img.src = b.src || b.text || ''; img.style.cssText = 'width:100%; height:100%; object-fit:fill; pointer-events:none; display:block;';
            if (!img.src) {
                el.style.cssText += 'border:2px dashed #9ca3af; background:#f3f4f6; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer; color:#6b7280;';
                if (!b.height_pct) el.style.height = '15%'; el.innerHTML = `<i class="fas fa-image" style="font-size:24px; margin-bottom:8px;"></i>`;
            } else { el.appendChild(img); }
        } else {
            // FIX: Use kebab-case for CSS properties
            let borderStyle = '';
            // Si es firma, agregamos borde superior para simular la línea
            if (b.type === 'signature') {
                borderStyle = `border-top: 2px solid ${b.color}; padding-top: 10px;`;
            }

            el.style.cssText += `font-size:${b.fontSize}px; color:${b.color}; font-weight:${b.bold ? 'bold' : 'normal'}; 
                                font-style:${b.italic ? 'italic' : 'normal'}; text-decoration:${b.underline ? 'underline' : 'none'}; 
                                font-family:${b.fontFamily}; text-align:${b.textAlign}; letter-spacing:${b.letterSpacing}px; 
                                white-space:pre-line; word-wrap:break-word; ${borderStyle}`;

            // Si es firma y el texto tiene los guiones bajos por defecto, los limpiamos para que solo quede el borde
            let finalText = b.text;
            if (b.type === 'signature' && finalText.includes('_____')) {
                finalText = finalText.replace(/_+/g, '').trim();
                // Si quedó vacío, poner placeholder
                if (!finalText) finalText = 'Firma del Responsable';
            }
            el.innerText = finalText;
        }
        makeDraggable(el); makeResizable(el); canvas.appendChild(el);
        if (list) {
            const card = document.createElement('div'); card.className = 'block-card' + (selectedId === b.id ? ' active' : '');
            let ct = b.type === 'image' ? 'Imagen' : b.text.substring(0, 20);
            card.innerHTML = `<div style="font-size:9px;">${b.type.toUpperCase()}</div><div style="font-weight:600;">${ct}</div>`;
            card.onclick = () => { select(b.id); switchTab('props'); }; list.appendChild(card);
        }
    });
}

function select(id) {
    selectedId = id; const b = blocks.find(b => b.id === id); render();
    if (b) {
        document.getElementById('no-selection').style.display = 'none'; document.getElementById('props-panel').style.display = 'block';
        const isImg = b.type === 'image';
        ['text', 'fontFamily', 'color', 'btnBold'].forEach(i => {
            const n = document.getElementById(i); if (!n) return;
            const g = i === 'btnBold' ? n.parentElement.parentElement : n.parentElement;
            if (g) g.style.display = isImg ? 'none' : 'block';
        });
        if (document.getElementById('imageGroup')) document.getElementById('imageGroup').style.display = isImg ? 'block' : 'none';

        let valText = b.text;
        // Limpieza visual en el textarea tambien si es firma
        if (b.type === 'signature' && valText.includes('_____')) {
            valText = valText.replace(/_+/g, '').trim();
        }

        const txtEl = document.getElementById('text');
        if (txtEl) txtEl.value = valText;

        document.getElementById('fontSize').value = b.fontSize; document.getElementById('fontSizeVal').innerText = b.fontSize + 'px';
        document.getElementById('color').value = b.color; document.getElementById('fontFamily').value = b.fontFamily;
        document.getElementById('btnBold').classList.toggle('active', b.bold);
        document.getElementById('btnItalic').classList.toggle('active', b.italic);
        document.getElementById('btnUnderline').classList.toggle('active', b.underline);
        ['Left', 'Center', 'Right', 'Justify'].forEach(a => { document.getElementById('btn' + a)?.classList.toggle('active', b.textAlign === a.toLowerCase()); });
        document.getElementById('rotation').value = b.rotation; document.getElementById('rotationVal').innerText = b.rotation + '°';
        document.getElementById('opacity').value = b.opacity; document.getElementById('opacityVal').innerText = Math.round(b.opacity * 100) + '%';
        document.getElementById('widthPct').value = Math.round(b.width_pct);
        document.getElementById('heightPct').value = b.height_pct ? Math.round(b.height_pct) : '';
        const ng = document.getElementById('nameFormatGroup'); if (ng) { ng.style.display = (b.type === 'student' ? 'block' : 'none'); document.getElementById('nameFormat').value = b.nameFormat || 'full'; }
    } else {
        document.getElementById('no-selection').style.display = 'block'; document.getElementById('props-panel').style.display = 'none';
    }
}

function updateElement(id) {
    const b = blocks.find(b => b.id === id), el = document.getElementById(id);
    if (el && b) {
        el.style.left = b.x_pct + '%'; el.style.top = b.y_pct + '%';
        el.style.transform = `rotate(${b.rotation}deg)`; el.style.width = b.width_pct + '%';
        if (b.height_pct) el.style.height = b.height_pct + '%'; else if (b.type !== 'image') el.style.height = 'auto';
        if (b.type !== 'image') {

            let borderStyle = '';
            if (b.type === 'signature') {
                borderStyle = `border-top: 2px solid ${b.color}; padding-top: 10px;`;
            }

            el.style.fontSize = b.fontSize + 'px'; el.style.color = b.color; el.style.fontFamily = b.fontFamily;
            el.style.textAlign = b.textAlign; el.style.letterSpacing = b.letterSpacing + 'px'; el.style.opacity = b.opacity;

            // Clean text for signature
            let finalText = b.text;
            if (b.type === 'signature' && finalText.includes('_____')) {
                finalText = finalText.replace(/_+/g, '').trim();
            }
            el.innerText = finalText;

            el.style.lineHeight = '1';
            el.style.cssText += borderStyle; // Append border style specifically
        }
    }
}

function makeDraggable(el) {
    let active = false, sX, sY, iX, iY;
    el.addEventListener('mousedown', (e) => {
        if (e.target.classList.contains('resize-handle')) return;
        active = true; sX = e.clientX; sY = e.clientY;
        const b = blocks.find(b => b.id === el.id); iX = b.x_pct; iY = b.y_pct;
        el.style.cursor = 'grabbing'; e.stopPropagation();
    });
    document.addEventListener('mousemove', (e) => {
        if (!active) return;
        const dx = (e.clientX - sX) / zoom, dy = (e.clientY - sY) / zoom;
        const b = blocks.find(b => b.id === el.id); if (!b) return;
        b.x_pct = iX + (dx / naturalW) * 100; b.y_pct = iY + (dy / naturalH) * 100;
        el.style.left = b.x_pct + '%'; el.style.top = b.y_pct + '%';
    });
    document.addEventListener('mouseup', () => { active = false; el.style.cursor = 'move'; });
}

function makeResizable(el) {
    const hs = ['nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'], cs = { 'nw': 'nw-resize', 'ne': 'ne-resize', 'sw': 'sw-resize', 'se': 'se-resize', 'n': 'n-resize', 's': 's-resize', 'e': 'e-resize', 'w': 'w-resize' };
    hs.forEach(p => {
        const h = document.createElement('div'); h.className = `resize-handle resize-${p}`; h.style.cursor = cs[p];
        let res = false, sX, sY, iW, iH;
        h.addEventListener('mousedown', (e) => {
            res = true; sX = e.clientX; sY = e.clientY;
            const b = blocks.find(b => b.id === el.id); iW = b.width_pct; iH = b.height_pct || (el.offsetHeight / naturalH * 100);
            e.stopPropagation(); e.preventDefault();
        });
        document.addEventListener('mousemove', (e) => {
            if (!res) return;
            const dx = (e.clientX - sX) / zoom, dy = (e.clientY - sY) / zoom, b = blocks.find(b => b.id === el.id); if (!b) return;
            if (p.includes('e')) b.width_pct = Math.max(1, iW + (dx / naturalW * 100)); else if (p.includes('w')) b.width_pct = Math.max(1, iW - (dx / naturalW * 100));
            if (p.includes('s')) b.height_pct = Math.max(1, iH + (dy / naturalH * 100)); else if (p.includes('n')) b.height_pct = Math.max(1, iH - (dy / naturalH * 100));
            el.style.width = b.width_pct + '%'; if (b.height_pct) el.style.height = b.height_pct + '%';
        });
        document.addEventListener('mouseup', () => { res = false; }); el.appendChild(h);
    });
}

function setAlign(a) { if (selectedId) { const b = blocks.find(b => b.id === selectedId); b.textAlign = a; render(); select(selectedId); } }
function toggleBold() { if (selectedId) { const b = blocks.find(b => b.id === selectedId); b.bold = !b.bold; render(); select(selectedId); } }
function toggleItalic() { if (selectedId) { const b = blocks.find(b => b.id === selectedId); b.italic = !b.italic; render(); select(selectedId); } }
function toggleUnderline() { if (selectedId) { const b = blocks.find(b => b.id === selectedId); b.underline = !b.underline; render(); select(selectedId); } }
// FIX: Renombrado a deleteBlock para coincidir con el HTML
function deleteBlock() {
    if (selectedId) {
        blocks = blocks.filter(b => b.id !== selectedId);
        selectedId = null;
        render();
        select(null);
    }
}

function saveConfig() {
    if (!bg) return;
    const config = {};
    blocks.forEach(b => {
        let ts = b.text;
        if (DEFAULTS[b.type]?.text === b.text && PLACEHOLDERS[b.type]) ts = PLACEHOLDERS[b.type];
        if (b.type === 'student') ts = '[NOMBRE DEL ESTUDIANTE]';
        config[b.id] = {
            x_px: (b.x_pct / 100) * naturalW, y_px: (b.y_pct / 100) * naturalH,
            width_px: (b.width_pct / 100) * naturalW, height_px: b.height_pct ? ((b.height_pct / 100) * naturalH) : undefined,
            image_w: naturalW, image_h: naturalH, font_size: b.fontSize, color: b.color,
            bold: !!b.bold, italic: !!b.italic, underline: !!b.underline, type: b.type, text_override: ts, src: b.src || (b.type === 'image' ? ts : ''),
            fontFamily: b.fontFamily,
            font_family: b.fontFamily,
            textAlign: b.textAlign,
            text_align: b.textAlign,
            letterSpacing: b.letterSpacing || 0,
            letter_spacing: b.letterSpacing || 0,
            rotation: b.rotation || 0,
            opacity: b.opacity !== undefined ? b.opacity : 1, name_format: b.nameFormat || 'full'
        };
    });
    document.getElementById('config').value = JSON.stringify(config);
    document.getElementById('saveForm').submit();
}