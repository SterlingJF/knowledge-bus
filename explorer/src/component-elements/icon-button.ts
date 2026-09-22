import { icon } from './icon';

export function iconButton(name: string, label: string, action: (event: MouseEvent) => void): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.setAttribute('aria-label', label);
  button.title = label;
  button.append(icon(name));
  button.addEventListener('click', action);
  return button;
}

export function labelledButton(name: string | null, label: string, action: (event: MouseEvent) => void): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  if (name) button.append(icon(name));
  const text = document.createElement('span');
  text.textContent = label;
  button.append(text);
  button.addEventListener('click', action);
  return button;
}
