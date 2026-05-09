/* Animaciones genericas (F12.1 + F12.3).
 *
 * Exportaciones:
 * - initRevealOnScroll(): activa el patron .reveal-on-scroll mediante
 *   IntersectionObserver. Cualquier elemento con esa clase recibe
 *   .is-visible cuando entra en viewport (threshold 0.15) y la
 *   transicion la define el CSS.
 * - animateCounter(el, target, duration, easing, format): cuenta de 0
 *   al target en `duration` ms con la curva `easing`, escribiendo
 *   en el elemento el resultado formateado. Pensado para los
 *   stat-counters de la landing.
 * - easeOutQuart: curva default para counters (parte rapida y se
 *   relaja al final).
 * - initPageTransitions(): F12.3d. Intercepta clicks en links
 *   internos y aplica fade-out antes de navegar; en cada page load
 *   hace fade-in. Excluye links externos, anchors y hash links.
 */

/* IntersectionObserver perezoso (compartido). */
let _revealObs = null;

export function initRevealOnScroll() {
  if (_revealObs) return _revealObs;
  if (typeof IntersectionObserver === 'undefined') {
    // Fallback navegadores muy antiguos: marca todo como visible.
    document.querySelectorAll('.reveal-on-scroll').forEach(el => {
      el.classList.add('is-visible');
    });
    return null;
  }
  _revealObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        _revealObs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal-on-scroll').forEach(el => _revealObs.observe(el));
  return _revealObs;
}

export const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4);

/* Anima un valor numerico de 0 al target en `duration` ms.
 * format(v) -> string que se escribe en `el.textContent`. */
export function animateCounter(el, target, duration = 1500, easing = easeOutQuart, format = (v) => Math.round(v).toString()) {
  const start = performance.now();
  function step(now) {
    const t = Math.min(1, (now - start) / duration);
    const eased = easing(t);
    el.textContent = format(target * eased);
    if (t < 1) requestAnimationFrame(step);
    else el.textContent = format(target);
  }
  requestAnimationFrame(step);
}

/* F12.3d: page transition fade entre navegaciones internas. */
export function initPageTransitions() {
  // Fade-in al cargar la pagina (body arranca opacity 1 por CSS,
  // pero si venimos del fade-out hay que asegurarse).
  document.body.removeAttribute('data-page-fade');

  // Interceptar clicks en links internos.
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href) return;
    // Ignorar: links externos, anchors a la misma pagina, mailto/tel,
    // descargas, target=_blank, modificadores de teclado (ctrl/cmd
    // click para nueva pestana).
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
    if (a.target === '_blank') return;
    if (a.hasAttribute('download')) return;
    if (href.startsWith('http://') || href.startsWith('https://')) {
      // Solo aplicar fade si el host coincide (link absoluto a misma app).
      try {
        const url = new URL(href, location.href);
        if (url.origin !== location.origin) return;
      } catch (_) { return; }
    }
    if (href.startsWith('#')) return;          // anchor en la misma pagina
    if (href.startsWith('mailto:') || href.startsWith('tel:')) return;
    if (href.startsWith('javascript:')) return;

    // Aplica fade-out y luego navega. preventDefault para tomar el
    // control. La duracion (200ms) coincide con el CSS transition de body.
    e.preventDefault();
    document.body.dataset.pageFade = 'out';
    setTimeout(() => { window.location.href = a.href; }, 180);
  });

  // Si el usuario vuelve via back button, restaurar opacity (Safari
  // a veces conserva el data-attr en bfcache).
  window.addEventListener('pageshow', (e) => {
    if (e.persisted) document.body.removeAttribute('data-page-fade');
  });
}
