import { type Entity, type ExplorerModel, human } from './model';

export const ICON_GRID = 24;
export const MONOGRAM_TYPE_SIZE = 13;

export const paths: Record<string, string> = {
  close: 'M6 6l12 12M18 6 6 18',
  menu: 'M4 6h16M4 12h16M4 18h16',
  search: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l6 6',
  share: 'M12 16V3m-5 5 5-5 5 5M4 14v7h16v-7',
  copy: 'M9 9h11v11H9ZM5 15H4V4h11v1',
  image: 'M3 4h18v16H3ZM3 16l5-5 4 4 3-3 6 6',
  vector: 'M4 4h4v4H4ZM16 16h4v4h-4ZM8 6h8M18 8v8',
  map: 'M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2ZM9 3v16M15 5v16',
  fit: 'M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6',
  plus: 'M12 5v14M5 12h14',
  minus: 'M5 12h14',
  actual: 'M4 4h16v16H4ZM9 9h6v6H9',
  back: 'M11 5l-7 7 7 7M4 12h16',
  forward: 'M13 5l7 7-7 7M20 12H4',
  chevron: 'M9 5l7 7-7 7',
  'chevron-down': 'm6 9 6 6 6-6',
  filter: 'M3 5h18l-7 8v6l-4-2v-4Z',
  options: 'M4 6h16M4 12h16M4 18h16M9 4v4M15 10v4M7 16v4',
  reset: 'M3 3v6h6M4 9a9 9 0 1 1-1 6',
  clear: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20M5 5l14 14',
  check: 'M4 12l5 5L20 6',
  network: 'M9 3h6v6H9ZM2 15h6v6H2ZM16 15h6v6h-6M12 9v3M5 15v-3h14v3',
  artifacts: 'M4 4h16v16H4Z',
  combined: 'M3 4h18v4H3ZM3 10h8v10H3ZM13 10h8v10h-8Z',
  sun: 'M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10M12 1v3M12 20v3M1 12h3M20 12h3M4 4l2 2M18 18l2 2M4 20l2-2M18 6l2-2',
  moon: 'M20 14a8 8 0 1 1-10-10 7 7 0 0 0 10 10Z',
  frame: 'M4 4h16v16H4ZM8 8h8v8H8',
  factor: 'M12 3l9 6-9 6-9-6ZM3 15l9 6 9-6',
  artifact: 'M5 2h10l4 4v16H5ZM14 2v5h5M8 12h8M8 16h8',
  element: 'M12 2 22 12 12 22 2 12Z',
  rule: 'M4 4h16v16H4ZM8 12h8',
};

export type Mark = { glyph: string } | { monogram: string };

const wordsOf = (label: string): string[] => label.split(/[^\p{L}\p{N}]+/u).filter(Boolean);

function monogramsAvailableTo(label: string): string[] {
  const words = wordsOf(label);
  const first = words[0] ?? '';
  if (!first) return [];
  const head = first[0].toUpperCase();
  const available = words.slice(1).map((word) => head + word[0].toUpperCase());
  for (let index = 1; index < first.length; index += 1) available.push(head + first[index].toLowerCase());
  if (!available.length) available.push(head);
  for (let ordinal = 2; ordinal <= 9; ordinal += 1) available.push(head + String(ordinal));
  return available;
}

export interface ModelMarks {
  frame(sourceId: string, fallback?: string): Mark;
  value(frameId: string, value: string, fallback?: string): Mark;
}

export const markableConcepts = (model: ExplorerModel): Entity[] => {
  const drawnBeforeItsPeers = (entity: Entity) =>
    entity.kind === 'frame' || entity.kind === 'factor' ? 0 : entity.frameId === model.orderingFrameId ? 1 : 2;
  return model.entities
    .filter((entity) => entity.kind === 'frame' || entity.kind === 'factor' || entity.kind === 'option')
    .sort((a, b) => drawnBeforeItsPeers(a) - drawnBeforeItsPeers(b) || a.label.localeCompare(b.label));
};

const marksBuiltForModel = new WeakMap<ExplorerModel, ModelMarks>();

export function marksOf(model: ExplorerModel): ModelMarks {
  const already = marksBuiltForModel.get(model);
  if (already) return already;
  const universeDeclared = model.marks?.declared ?? {};
  const taken = new Set<string>();
  for (const mark of Object.values(universeDeclared)) if ('monogram' in mark) taken.add(mark.monogram);
  const monogramOfLabel = new Map<string, string>();
  const frameConcepts = new Map<string, Entity>();
  const valueConcepts = new Map<string, Entity>();
  for (const concept of markableConcepts(model)) {
    if (concept.kind === 'option') valueConcepts.set(`${concept.frameId ?? ''} ${concept.sourceId}`, concept);
    else frameConcepts.set(concept.sourceId, concept);
    if (universeDeclared[concept.id] || monogramOfLabel.has(concept.label)) continue;
    const chosen = monogramsAvailableTo(concept.label).find((candidate) => !taken.has(candidate));
    if (!chosen) continue;
    taken.add(chosen);
    monogramOfLabel.set(concept.label, chosen);
  }
  const markOf = (concept: Entity | undefined, label: string, fallback: string): Mark => {
    const declared = concept && universeDeclared[concept.id];
    if (declared) return declared;
    const assigned = monogramOfLabel.get(label) ?? monogramsAvailableTo(label)[0];
    return assigned ? { monogram: assigned } : { glyph: paths[fallback] ?? paths.frame };
  };
  const marks: ModelMarks = {
    frame: (sourceId, fallback = 'frame') => {
      const concept = frameConcepts.get(sourceId);
      return markOf(concept, concept?.label ?? human(sourceId), fallback);
    },
    value: (frameId, value, fallback = 'frame') => {
      const concept = valueConcepts.get(`${frameId} ${value}`);
      return markOf(concept, concept?.label ?? human(value), fallback);
    },
  };
  marksBuiltForModel.set(model, marks);
  return marks;
}
