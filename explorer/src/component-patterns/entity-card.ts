import { cardSurface } from '../component-elements/card-surface';
import { markIcon } from '../component-elements/icon';
import { type PlacedCard } from '../lib/layout';
import { type ExplorerModel } from '../lib/model';
import { cardAnatomy, type TextMeasurer } from '../lib/card';

export function entityCard(
  card: PlacedCard,
  model: ExplorerModel,
  select: (id: string) => void,
  measure?: TextMeasurer,
): HTMLButtonElement {
  const anatomy = cardAnatomy(card, model, measure);
  const surface = cardSurface(card.id, card.kind, card, anatomy.title, () => select(card.id));

  if (card.kind === 'element' && anatomy.icon) {
    const badge = document.createElement('span');
    badge.className = 'card-order-icon';
    badge.setAttribute('aria-label', anatomy.subtitle ? `${anatomy.title}, ${anatomy.subtitle}` : anatomy.title);
    badge.append(markIcon(anatomy.icon));
    surface.append(badge);
  }

  const title = document.createElement('strong');
  title.className = 'card-title';
  title.dataset.part = 'card-heading';
  if (anatomy.icon && card.kind !== 'element') title.append(markIcon(anatomy.icon));
  const titleText = document.createElement('span');
  titleText.textContent = anatomy.title;
  title.append(titleText);
  surface.append(title);

  if (anatomy.subtitle) {
    const subtitle = document.createElement('span');
    subtitle.className = 'card-subtitle';
    subtitle.dataset.part = 'card-heading';
    subtitle.textContent = anatomy.subtitle;
    surface.append(subtitle);
  }

  if (anatomy.match) {
    const match = document.createElement('span');
    match.className = 'card-match';
    match.textContent = anatomy.match;
    surface.append(match);
  }

  if (anatomy.frameIcons.length) {
    const row = document.createElement('span');
    row.className = 'card-frames';
    row.setAttribute('aria-label', `Referenced frames: ${anatomy.frameNames.join(', ')}`);
    anatomy.frameIcons.forEach((name, index) => {
      const slot = document.createElement('span');
      slot.title = anatomy.frameNames[index];
      slot.append(markIcon(name, anatomy.frameNames[index]));
      row.append(slot);
    });
    if (anatomy.overflow) {
      const overflow = document.createElement('span');
      overflow.className = 'card-frames-overflow';
      overflow.textContent = anatomy.overflow;
      overflow.setAttribute('aria-label', anatomy.frameNames.slice(anatomy.frameIcons.length).join(', '));
      row.append(overflow);
    }
    surface.append(row);
    surface.title = anatomy.frameNames.join(' · ');
  }
  return surface;
}

export function optionCard(
  card: PlacedCard,
  model: ExplorerModel,
  stats: { artifacts: number; elements: number },
  select: (id: string) => void,
): HTMLButtonElement {
  const anatomy = cardAnatomy(card, model);
  const surface = cardSurface(card.id, 'option', card, anatomy.title, () => select(card.id));
  if (anatomy.icon) surface.append(markIcon(anatomy.icon));
  const title = document.createElement('strong');
  title.className = 'card-title';
  title.dataset.part = 'card-heading';
  title.textContent = anatomy.title;
  surface.append(title);
  if (anatomy.subtitle) {
    const question = document.createElement('span');
    question.className = 'card-subtitle';
    question.dataset.part = 'card-heading';
    question.textContent = anatomy.subtitle;
    surface.append(question);
  }
  const counts = document.createElement('span');
  counts.className = 'card-stats';
  counts.textContent = `${stats.artifacts} Artifacts  ${stats.elements} Elements`;
  surface.append(counts);
  return surface;
}
