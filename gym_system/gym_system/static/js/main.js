// Colombia time display
function updateColombiaTime() {
    const now = new Date();
    const opts = { timeZone: 'America/Bogota', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };
    const timeStr = now.toLocaleTimeString('es-CO', opts);
    const dateOpts = { timeZone: 'America/Bogota', day: '2-digit', month: '2-digit', year: 'numeric' };
    const dateStr = now.toLocaleDateString('es-CO', dateOpts);
    document.querySelectorAll('#colombiaTime, #footerTime').forEach(el => {
        if (el) el.textContent = `${dateStr} ${timeStr}`;
    });
}
updateColombiaTime();
setInterval(updateColombiaTime, 1000);

// Auto-dismiss alerts
document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => el.classList.remove('show'), 4000);
});

// Confirm delete buttons
document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
        if (!confirm(btn.dataset.confirm)) e.preventDefault();
    });
});
