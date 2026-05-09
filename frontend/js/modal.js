/* Modal de confirmacion accesible.
 *
 * Uso:
 *   const ok = await confirmModal({
 *     title: '¿Borrar?', body: 'Texto explicativo',
 *     confirmLabel: 'Borrar', confirmVariant: 'danger', icon: 'trash-2',
 *   });
 *   if (ok) { ... }
 *
 * Sin dependencias. El nodo se crea al vuelo, se muestra con
 * animacion y se elimina al cerrar. Esc y click en backdrop cancelan.
 */

const ICONS = {
  'trash-2': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/></svg>',
};

export function confirmModal({
  title,
  body,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  confirmVariant = 'primary',  // 'primary' | 'danger'
  icon = null,
} = {}) {
  return new Promise((resolve) => {
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    const iconHtml = icon && ICONS[icon] ? `<span class="modal-icon modal-icon-${confirmVariant}">${ICONS[icon]}</span>` : '';
    backdrop.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-head">
          ${iconHtml}
          <h3 class="modal-title"></h3>
        </div>
        <p class="modal-body"></p>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" data-action="cancel"></button>
          <button type="button" class="btn btn-${confirmVariant}" data-action="confirm">
            ${icon && ICONS[icon] ? ICONS[icon] : ''}
            <span></span>
          </button>
        </div>
      </div>`;
    backdrop.querySelector('.modal-title').textContent = String(title || '');
    backdrop.querySelector('.modal-body').textContent = String(body || '');
    backdrop.querySelector('[data-action="cancel"]').textContent = cancelLabel;
    backdrop.querySelector('[data-action="confirm"] span').textContent = confirmLabel;

    document.body.appendChild(backdrop);
    // Reflow para activar la animacion.
    backdrop.offsetHeight;
    backdrop.classList.add('modal-show');

    const finish = (value) => {
      backdrop.classList.remove('modal-show');
      backdrop.classList.add('modal-hide');
      const cleanup = () => {
        backdrop.remove();
        document.removeEventListener('keydown', onKey);
        resolve(value);
      };
      backdrop.addEventListener('transitionend', cleanup, { once: true });
      setTimeout(() => backdrop.isConnected && cleanup(), 400);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') finish(false);
      else if (e.key === 'Enter') finish(true);
    };
    document.addEventListener('keydown', onKey);
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) finish(false);
    });
    backdrop.querySelector('[data-action="cancel"]').addEventListener('click', () => finish(false));
    backdrop.querySelector('[data-action="confirm"]').addEventListener('click', () => finish(true));

    // Foco inicial en cancelar (mas seguro que en el destructivo).
    setTimeout(() => backdrop.querySelector('[data-action="cancel"]').focus(), 0);
  });
}
