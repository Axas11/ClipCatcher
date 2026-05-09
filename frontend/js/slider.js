/* Slider component (F10.1).
 *
 * Construye un slider tematizado con label uppercase, valor formateado
 * a la derecha, tooltip flotante encima del thumb y marcas min/max
 * debajo. La posicion del tooltip se actualiza en cada `input` event.
 *
 * Uso:
 *   import { mountSlider } from './slider.js';
 *   const s = mountSlider({
 *     label: 'Ventana de encadenamiento',
 *     hint: 'Tiempo maximo entre kills agrupadas en un mismo clip.',
 *     min: 1, max: 60, step: 0.5, value: 6,
 *     format: (v) => `${v.toFixed(1)} s`,
 *     onChange: (v) => console.log(v),
 *   });
 *   container.appendChild(s.element);
 *   s.getValue();   // 6
 *   s.setValue(12);
 */

let _idCounter = 0;
const defaultFormat = (v) => `${v}`;

export function mountSlider(opts) {
  const {
    label = '',
    hint = '',
    min = 0,
    max = 100,
    step = 1,
    value = 0,
    format = defaultFormat,
    onChange = null,
  } = opts;

  _idCounter += 1;
  const sliderId = `slider-${_idCounter}`;

  const root = document.createElement('div');
  root.className = 'slider-input';
  root.innerHTML = `
    <div class="slider-head">
      <label class="field-label" for="${sliderId}"></label>
      <span class="slider-value"></span>
    </div>
    <div class="slider-track-wrap">
      <input type="range" class="slider" id="${sliderId}"
             min="${min}" max="${max}" step="${step}" value="${value}">
      <span class="slider-tooltip"></span>
    </div>
    <div class="slider-marks">
      <span>${format(min)}</span>
      <span>${format(max)}</span>
    </div>
    <p class="field-hint"></p>`;

  const labelEl = root.querySelector('.field-label');
  const valueEl = root.querySelector('.slider-value');
  const inputEl = root.querySelector('input.slider');
  const tooltipEl = root.querySelector('.slider-tooltip');
  const hintEl = root.querySelector('.field-hint');

  labelEl.textContent = label;
  hintEl.textContent = hint;
  if (!hint) hintEl.style.display = 'none';

  const updateUI = (v) => {
    const formatted = format(v);
    valueEl.textContent = formatted;
    tooltipEl.textContent = formatted;
    // Posicion del tooltip: pct entre min y max. Aceptamos ±~10px de
    // deriva en los extremos por el tamano finito del thumb (20px); a
    // efectos visuales no se nota porque el tooltip queda centrado
    // sobre el thumb dentro del rango interno y la transicion es suave.
    const pct = (Number(v) - Number(min)) / (Number(max) - Number(min));
    tooltipEl.style.left = `${pct * 100}%`;
  };

  inputEl.addEventListener('input', () => {
    const v = parseFloat(inputEl.value);
    updateUI(v);
    if (typeof onChange === 'function') onChange(v);
  });

  // Mostrar tooltip mientras el slider tiene foco activo (drag de teclado).
  inputEl.addEventListener('focus', () => root.classList.add('is-active'));
  inputEl.addEventListener('blur', () => root.classList.remove('is-active'));
  // Idem para mousedown sostenido (algunos navegadores no disparan focus).
  inputEl.addEventListener('mousedown', () => root.classList.add('is-active'));
  inputEl.addEventListener('mouseup', () => root.classList.remove('is-active'));
  inputEl.addEventListener('touchstart', () => root.classList.add('is-active'), { passive: true });
  inputEl.addEventListener('touchend', () => root.classList.remove('is-active'));

  // Estado inicial.
  updateUI(value);

  return {
    element: root,
    getValue: () => parseFloat(inputEl.value),
    setValue: (v) => {
      inputEl.value = String(v);
      updateUI(parseFloat(inputEl.value));
    },
    inputEl,
  };
}
