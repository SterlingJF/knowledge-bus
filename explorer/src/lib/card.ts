import { type ExplorerModel, type Entity, human, referencedFrames } from './model';
import { type PlacedCard } from './layout';
import { cardinalityCopy, setByCopy } from './phrasing';
import { marksOf, type Mark } from './icons';
import { tokenNumber } from './tokens';

export type TextMeasurer = (text: string, size: number) => number;

const AVERAGE_GLYPH_RATIO = 0.55;
export const approximateText: TextMeasurer = (text, size) => text.length * size * AVERAGE_GLYPH_RATIO;

export const MAX_FRAME_ICONS = 3;

export interface CardAnatomy {
  accent: string;
  edge: 'top' | 'left';
  icon: Mark | null;
  title: string;
  titleLines: string[];
  subtitle: string;
  subtitleLines: string[];
  frameIcons: Mark[];
  frameNames: string[];
  overflow: string;
  match: string;
}

export function wrap(text: string, width: number, size: number, measure: TextMeasurer = approximateText): string[] {
  const lines: string[] = [];
  let line = '';
  for (const word of text.split(/\s+/).filter(Boolean)) {
    if (line && measure(line + ' ' + word, size) > width) {
      lines.push(line);
      line = word;
    } else line += (line ? ' ' : '') + word;
  }
  if (line) lines.push(line);
  return lines;
}

function subtitleFor(card: PlacedCard, entity: Entity | null, model: ExplorerModel): string {
  if (card.kind === 'rule') return 'No artifact contents are required in this context.';
  if (!entity) return '';
  if (entity.kind === 'element') return cardinalityCopy(entity.raw.cardinality);
  if (entity.kind === 'frame' || entity.kind === 'factor') return entity.description || setByCopy(entity.raw.set_by);
  if (entity.kind === 'option') return entity.description;
  return '';
}

function matchFor(card: PlacedCard, model: ExplorerModel): string {
  if (card.kind !== 'frame') return '';
  const rule = model.rules[0];
  const values = (rule?.raw.when ?? {})[card.entity?.sourceId ?? ''] as string[] | undefined;
  return values ? values.map(human).join(' or ') : '';
}

export function cardAnatomy(card: PlacedCard, model: ExplorerModel, measure: TextMeasurer = approximateText): CardAnatomy {
  const entity = card.entity;
  const accent =
    card.kind === 'artifact'
      ? '--kb-artifact'
      : card.kind === 'element'
        ? '--kb-element'
        : card.kind === 'rule'
          ? '--kb-border'
          : '--kb-frame';
  const ordering = model.orderingFrameId.split(':').slice(1).join(':');
  const marks = marksOf(model);
  const icon =
    card.kind === 'element'
      ? marks.value(model.orderingFrameId, String(entity?.frameValues[ordering] ?? entity?.raw[ordering] ?? ''), 'element')
      : card.kind === 'option'
        ? marks.value(entity?.frameId ?? '', entity?.sourceId ?? '', 'frame')
        : card.kind === 'frame' || card.kind === 'factor'
          ? marks.frame(entity?.sourceId ?? '', card.kind)
          : null;
  const title = card.kind === 'rule' ? 'No artifact needed' : (entity?.label ?? human(card.id.split(':').pop() ?? ''));
  const subtitle = subtitleFor(card, entity, model);
  const frameNames =
    entity && (entity.kind === 'element' || entity.kind === 'artifact')
      ? referencedFrames(model, entity.id).filter((frame) => frame !== ordering)
      : [];
  const padding = tokenNumber('--kb-space-3');
  const iconSize = tokenNumber('--kb-icon-base');
  const textWidth = card.w - padding * 2 - (icon ? iconSize + tokenNumber('--kb-space-2') : 0);
  return {
    accent,
    edge: card.kind === 'artifact' || card.kind === 'frame' || card.kind === 'factor' ? 'top' : 'left',
    icon,
    title,
    titleLines: wrap(title, textWidth, tokenNumber('--kb-card-text'), measure),
    subtitle,
    subtitleLines: wrap(subtitle, textWidth, tokenNumber('--kb-type-body-sm'), measure),
    frameIcons: frameNames.slice(0, MAX_FRAME_ICONS).map((frame) => marks.frame(frame)),
    frameNames: frameNames.map(human),
    overflow: frameNames.length > MAX_FRAME_ICONS ? `+${frameNames.length - MAX_FRAME_ICONS}` : '',
    match: matchFor(card, model),
  };
}
