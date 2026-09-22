import { type Rect } from '../lib/geometry';

export type CardState = 'idle' | 'selected' | 'hushed' | 'dimmed';

export function cardSurface(id: string, kind: string, box: Rect, label: string, action: (event: MouseEvent) => void): HTMLButtonElement {
  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'card';
  card.dataset.id = id;
  card.dataset.kind = kind;
  card.dataset.state = 'idle';
  card.dataset.preview = 'false';
  card.setAttribute('aria-label', label);
  card.setAttribute('aria-pressed', 'false');
  card.style.left = `${box.x}px`;
  card.style.top = `${box.y}px`;
  card.style.width = `${box.w}px`;
  card.style.height = `${box.h}px`;
  card.addEventListener('click', (event) => {
    event.stopPropagation();
    action(event);
  });
  return card;
}

export function setCardState(card: HTMLElement, state: CardState, preview = false) {
  card.dataset.state = state;
  card.dataset.preview = String(preview);
  card.setAttribute('aria-pressed', String(state === 'selected'));
}
