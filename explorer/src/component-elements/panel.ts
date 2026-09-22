import { iconButton } from './icon-button';

export interface Panel {
  root: HTMLElement;
  head: HTMLElement;
  body: HTMLElement;
  title: HTMLElement;
}

export function panel(className: string, label: string, onClose: () => void): Panel {
  const root = document.createElement('aside');
  root.className = `panel ${className}`;
  root.setAttribute('aria-label', label);
  const head = document.createElement('header');
  head.className = 'panel-head';
  const title = document.createElement('strong');
  const close = iconButton('close', 'Close', onClose);
  close.classList.add('close');
  head.append(title, close);
  const body = document.createElement('div');
  body.className = 'panel-body';
  root.append(head, body);
  return { root, head, body, title };
}
