import { markIcon } from './icon';
import { type Mark } from '../lib/icons';

export function chip(value: string, label: string, pressed: boolean, glyph: Mark | null, toggle: () => void): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'chip';
  button.dataset.value = value;
  button.setAttribute('aria-pressed', String(pressed));
  if (glyph) button.append(markIcon(glyph));
  const text = document.createElement('span');
  text.textContent = label;
  button.append(text);
  button.addEventListener('click', toggle);
  return button;
}
