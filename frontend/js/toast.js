/* Sistema de notificaciones tipo toast.
 *
 * Llamada: showToast("mensaje", "success" | "error" | "info" | "warning", durationMs)
 *
 * El contenedor (top-right, fixed) se crea perezosamente la primera vez
 * que se invoca un toast. Cada toast es un nodo independiente: anima
 * entrada, vive `duration` ms, anima salida y se autodestruye. Si llegan
 * varios a la vez se apilan verticalmente.
 *
 * No depende de Lucide en runtime: el icono se inyecta como SVG inline
 * para que el toast sea autosuficiente y se pinte instantaneamente
 * (Lucide hace replace tras `createIcons()`, lo que en un toast efimero
 * se nota).
 */

const ICONS = {
  success: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  error: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
  info: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
  warning: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
};

function _ensureContainer() {
  let c = document.getElementById('toast-container');
  if (!c) {
    c = document.createElement('div');
    c.id = 'toast-container';
    c.className = 'toast-container';
    document.body.appendChild(c);
  }
  return c;
}

export function showToast(message, type = 'info', duration = 3000) {
  if (!ICONS[type]) type = 'info';
  const container = _ensureContainer();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
  toast.innerHTML = `
    <span class="toast-icon">${ICONS[type]}</span>
    <span class="toast-msg"></span>
  `;
  // Asignamos texto via .textContent para evitar inyectar HTML del backend.
  toast.querySelector('.toast-msg').textContent = String(message);
  container.appendChild(toast);

  // Forzar reflow para que la transicion de entrada se aplique.
  // (sin esto, el navegador agruparia el "append" y el "add('show')" y
  //  nunca veriamos la animacion de slide-in).
  // eslint-disable-next-line no-unused-expressions
  toast.offsetHeight;
  toast.classList.add('toast-show');

  const remove = () => {
    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');
    // Esperamos a que termine la transicion CSS antes de remover el nodo.
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    // Fallback por si la transicion no dispara (display:none, etc.).
    setTimeout(() => toast.isConnected && toast.remove(), 600);
  };
  setTimeout(remove, Math.max(800, duration));
  toast.addEventListener('click', remove);

  return toast;
}
