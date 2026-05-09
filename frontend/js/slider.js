/* Slider component (F10.1, F10-fix #2).
 *
 * Construye un slider tematizado con label uppercase, valor formateado
 * a la derecha y marcas min/max debajo. El value display arriba a la
 * derecha es la unica representacion del valor — el tooltip flotante
 * sobre el thumb se elimino en F10-fix porque duplicaba el dato.
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
    </div>
    <div class="slider-marks">
      <span>${format(min)}</span>
      <span>${format(max)}</span>
    </div>
    <p class="field-hint"></p>`;

  const labelEl = root.querySelector('.field-label');
  const valueEl = root.querySelector('.slider-value');
  const inputEl = root.querySelector('input.slider');
  const hintEl = root.querySelector('.field-hint');

  labelEl.textContent = label;
  hintEl.textContent = hint;
  if (!hint) hintEl.style.display = 'none';

  const updateUI = (v) => {
    valueEl.textContent = format(v);
  };

  inputEl.addEventListener('input', () => {
    const v = parseFloat(inputEl.value);
    updateUI(v);
    if (typeof onChange === 'function') onChange(v);
  });

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
