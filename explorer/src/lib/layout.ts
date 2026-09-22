import { type ExplorerModel, type ViewOptions, type Entity, compositionEntries, human, relationEdges } from './model';
import { artifactEdges } from './rollup';
import { type Point, type Rect, union } from './geometry';
import { connectedLayout } from './connected-layout';

export interface PlacedCard extends Rect {
  id: string;
  entity: Entity | null;
  kind: 'artifact' | 'element' | 'frame' | 'factor' | 'rule' | 'option';
  scopeId: string;
}

export interface Boundary extends Rect {
  id: string;
  title: string;
  caption: string;
  role: 'section' | 'group' | 'scope';
  scopeId: string;
}

export interface Note extends Rect {
  id: string;
  text: string;
  scopeId: string;
}

export interface Layout {
  cards: PlacedCard[];
  boundaries: Boundary[];
  notes: Note[];
  bounds: Rect;
}

const CARD_W = 230;
const CARD_H = 104;
const FRAME_CARD_W = 245;
const FRAME_CARD_H = 150;
const RULE_CARD_W = 410;
const RULE_CARD_H = 118;
const OPTION_CARD_W = 165;
const OPTION_CARD_H = 166;

const SECTION_X = 40;
const SECTION_W = 1100;

const FRAMES_BOUNDARY = 'scope:frames';
const EXCEPTIONS_BOUNDARY = 'scope:rule';
const FACTORS_BOUNDARY = 'scope:factors';
const FRAMES_CAPTION = 'Your situation. These change what you need.';
const EXCEPTIONS_CAPTION = 'Your special cases. These mean no artifact is needed.';
const FACTORS_CAPTION = 'Your conditions. These shape how you go about the work.';
const FACTORS_NONE_DECLARED = 'This universe declares no factors.';

const FRAME_CARDS_X = 85;
const FRAME_CARDS_Y = 154;
const FRAME_COLUMNS = 4;
const FRAME_STEP_X = 265;
const FRAME_STEP_Y = 170;

const NESTED_X = 85;
const NESTED_W = 1040;

const ORDER_SCOPE_Y = 514;
const ORDER_SCOPE_H = 223;
const OPTIONS_X = 16;
const OPTIONS_Y = 37;
const OPTIONS_GAP = 12;

const RULE_CARD_X = 130;
const RULE_CARD_Y = 871;

const FACTOR_Y = 1105;
const FACTOR_H = 150;
const FACTOR_COLUMNS = 4;
const FACTOR_X = 20;
const FACTOR_TOP = 45;
const FACTOR_STEP_X = 265;
const FACTOR_STEP_Y = 115;
const FACTOR_CARD_H = 86;
const NOTE_H = 72;

const ARTIFACTS_X = 40;
const ARTIFACTS_Y = 60;
const ARTIFACT_COLUMNS = 9;
const ARTIFACT_CARD_X = 30;
const ARTIFACT_CARD_Y = 45;
const ARTIFACT_STEP_X = 263;
const ARTIFACT_STEP_Y = 136;
const ARTIFACTS_W = 2420;
const ARTIFACTS_H = 430;

const ELEMENTS_Y = 560;
const ELEMENTS_X = 0;
const ELEMENTS_W = 3660;
const ELEMENTS_H = 1900;
const PHASE_COLUMNS = 3;
const PHASE_X = 40;
const PHASE_Y = 40;
const PHASE_STEP_X = 1200;
const PHASE_STEP_Y = 850;
const PHASE_HEAD = 110;
const PHASE_CARD_COLUMNS = 4;
const PHASE_CARD_X = 30;
const PHASE_CARD_Y = 90;
const PHASE_CARD_STEP_X = 275;
const PHASE_CARD_STEP_Y = 122;

const FLAT_COLUMNS = 9;
const FLAT_X = 40;
const FLAT_Y = 60;
const FLAT_STEP_X = 300;
const FLAT_STEP_Y = 145;

const CONNECTED_CARD_W = 230;
const CONNECTED_CARD_H = 104;

const GAP_BETWEEN_CARD_COLUMNS = PHASE_CARD_STEP_X - CARD_W;
const GAP_BELOW_LAST_CARD_ROW = PHASE_HEAD + PHASE_CARD_STEP_Y - PHASE_CARD_Y - CARD_H;

interface Head extends Point {
  title: string;
  caption: string;
}

const sizeHolding = (box: Head, held: Rect[]): { w: number; h: number } => {
  const inside = union(held);
  return {
    w: Math.max(inside.x + inside.w + GAP_BETWEEN_CARD_COLUMNS, box.x + headingWidth(box)) - box.x,
    h: inside.y + inside.h + GAP_BELOW_LAST_CARD_ROW - box.y,
  };
};

const sizedToHold = (box: Boundary, held: Rect[]): Boundary => (held.length ? { ...box, ...sizeHolding(box, held) } : box);

const headDrop = (head: { caption: string }): number => (head.caption ? CAPTION_DROP : TITLE_DROP);

const placedToHold = (head: Omit<Boundary, keyof Rect>, held: Rect[]): Boundary => {
  const inside = union(held);
  const origin = { x: inside.x - GAP_BETWEEN_CARD_COLUMNS, y: inside.y - headDrop(head) - GAP_BELOW_LAST_CARD_ROW };
  return { ...head, ...origin, ...sizeHolding({ ...head, ...origin }, held) };
};

const notingWhatTheUniverseDeclaresNoneOf = (box: Boundary, text: string): Note => ({
  id: `${box.id}:none`,
  text,
  scopeId: box.id,
  x: box.x + GAP_BETWEEN_CARD_COLUMNS,
  y: box.y + headDrop(box) + GAP_BELOW_LAST_CARD_ROW,
  w: box.w - GAP_BETWEEN_CARD_COLUMNS * 2,
  h: NOTE_H,
});

const drawingOnlyWhatSomethingDeclares = (cards: PlacedCard[], boundaries: Boundary[], notes: Note[]): Layout => {
  const declared = new Set([...cards.map((c) => c.scopeId), ...notes.map((n) => n.scopeId)]);
  for (let growing = true; growing;) {
    growing = false;
    for (const boundary of boundaries)
      if (declared.has(boundary.id) && boundary.scopeId && !declared.has(boundary.scopeId)) {
        declared.add(boundary.scopeId);
        growing = true;
      }
  }
  const drawn = boundaries.filter((b) => declared.has(b.id));
  return { cards, boundaries: drawn, notes, bounds: union([...cards, ...drawn]) };
};

export function roleOfTheBoundaryEachCardStandsIn(layout: Layout): Map<string, Boundary['role']> {
  const roleOf = new Map(layout.boundaries.map((boundary) => [boundary.id, boundary.role]));
  const standing = new Map<string, Boundary['role']>();
  for (const card of layout.cards) {
    const role = roleOf.get(card.scopeId);
    if (role) standing.set(card.id, role);
  }
  return standing;
}

export function passesFrameFilter(model: ExplorerModel, id: string, filters: string[]): boolean {
  if (!filters.length) return true;
  const referenced = (frame: string) => model.wiring.some((w) => w.sourceFrameId === frame && (w.to === id || w.targetPair?.includes(id)));
  const optionMatches = (frame: string, value: string) =>
    model.wiring.some((w) => w.sourceFrameId === frame && (w.to === id || w.targetPair?.includes(id)) && w.value.includes(value));
  const groups = new Map<string, string[]>();
  for (const filter of filters) {
    const [kind, frame, ...rest] = filter.split(':');
    const key = kind === 'option' ? 'option:' + frame : filter;
    groups.set(key, [...(groups.get(key) ?? []), kind === 'option' ? rest.join(':') : '']);
  }
  const entity = model.entities.find((e) => e.id === id);
  for (const [key, values] of groups) {
    const [kind, frame] = key.split(':');
    if (kind === 'option') {
      const own = entity?.frameValues[frame];
      const matched = values.some(
        (value) =>
          own === value ||
          (!!own && typeof own === 'object' && Object.values(own as Record<string, unknown>).includes(value)) ||
          optionMatches(frame, value),
      );
      if (!matched) return false;
    } else if (!referenced(frame)) return false;
  }
  return true;
}

function orderingOptions(model: ExplorerModel): Entity[] {
  const frame = model.entities.find((e) => e.id === model.orderingFrameId);
  return model.entities.filter((e) => e.kind === 'option' && !!frame && e.id.startsWith('option:' + frame.sourceId + ':'));
}

function visibleElements(model: ExplorerModel, options: ViewOptions): Entity[] {
  return model.entities.filter((e) => e.kind === 'element' && passesFrameFilter(model, e.id, options.frames));
}

function visibleArtifacts(model: ExplorerModel, options: ViewOptions): Entity[] {
  return model.entities.filter((e) => e.kind === 'artifact' && passesFrameFilter(model, e.id, options.frames));
}

function framesLayout(model: ExplorerModel): Layout {
  const cards: PlacedCard[] = [];
  const insideFrames: Rect[] = [];
  const nested: Boundary[] = [];

  const framed = model.entities.filter((e) => e.kind === 'frame' && e.id !== model.orderingFrameId);
  framed.forEach((entity, index) => {
    const card: PlacedCard = {
      id: entity.id,
      entity,
      kind: 'frame',
      scopeId: FRAMES_BOUNDARY,
      x: FRAME_CARDS_X + (index % FRAME_COLUMNS) * FRAME_STEP_X,
      y: FRAME_CARDS_Y + Math.floor(index / FRAME_COLUMNS) * FRAME_STEP_Y,
      w: FRAME_CARD_W,
      h: FRAME_CARD_H,
    };
    cards.push(card);
    insideFrames.push(card);
  });

  const ordering = model.entities.find((e) => e.id === model.orderingFrameId);
  const options = orderingOptions(model);
  if (ordering && options.length) {
    const orderScope: Boundary = {
      id: model.orderingFrameId,
      title: ordering.label,
      caption: '',
      role: 'scope',
      scopeId: FRAMES_BOUNDARY,
      x: NESTED_X,
      y: ORDER_SCOPE_Y,
      w: NESTED_W,
      h: ORDER_SCOPE_H,
    };
    nested.push(orderScope);
    insideFrames.push(orderScope);
    const step = (NESTED_W - OPTIONS_X * 2 + OPTIONS_GAP) / options.length;
    options.forEach((entity, index) =>
      cards.push({
        id: entity.id,
        entity,
        kind: 'option',
        scopeId: model.orderingFrameId,
        x: NESTED_X + OPTIONS_X + index * step,
        y: ORDER_SCOPE_Y + OPTIONS_Y,
        w: Math.min(OPTION_CARD_W, step - OPTIONS_GAP),
        h: OPTION_CARD_H,
      }),
    );
  }

  const rule = model.rules[0];
  if (rule) {
    const ruleCard: PlacedCard = {
      id: rule.id,
      entity: null,
      kind: 'rule',
      scopeId: EXCEPTIONS_BOUNDARY,
      x: RULE_CARD_X,
      y: RULE_CARD_Y,
      w: RULE_CARD_W,
      h: RULE_CARD_H,
    };
    cards.push(ruleCard);
    const exceptions = placedToHold(
      { id: EXCEPTIONS_BOUNDARY, title: 'Exceptions', caption: EXCEPTIONS_CAPTION, role: 'section', scopeId: FRAMES_BOUNDARY },
      [ruleCard],
    );
    nested.push(exceptions);
    insideFrames.push(exceptions);
  }

  const boundaries: Boundary[] = insideFrames.length
    ? [
        placedToHold({ id: FRAMES_BOUNDARY, title: 'Frames', caption: FRAMES_CAPTION, role: 'section', scopeId: '' }, insideFrames),
        ...nested,
      ]
    : [];

  const factors = model.entities.filter((e) => e.kind === 'factor');
  const factorCards: PlacedCard[] = factors.map((entity, index) => ({
    id: entity.id,
    entity,
    kind: 'factor',
    scopeId: FACTORS_BOUNDARY,
    x: SECTION_X + FACTOR_X + (index % FACTOR_COLUMNS) * FACTOR_STEP_X,
    y: FACTOR_Y + FACTOR_TOP + Math.floor(index / FACTOR_COLUMNS) * FACTOR_STEP_Y,
    w: CARD_W,
    h: FACTOR_CARD_H,
  }));
  const factorsBox: Boundary = {
    id: FACTORS_BOUNDARY,
    title: 'Factors',
    caption: FACTORS_CAPTION,
    role: 'section',
    scopeId: '',
    x: SECTION_X,
    y: FACTOR_Y,
    w: SECTION_W,
    h: FACTOR_H,
  };
  const notes = factorCards.length ? [] : [notingWhatTheUniverseDeclaresNoneOf(factorsBox, FACTORS_NONE_DECLARED)];
  boundaries.push(sizedToHold(factorsBox, factorCards.length ? factorCards : notes));
  cards.push(...factorCards);
  return drawingOnlyWhatSomethingDeclares(cards, boundaries, notes);
}

function everyRolledPair(model: ExplorerModel, ids: string[]): { from: string; to: string }[] {
  const composition = compositionEntries(model);
  const relations = relationEdges(model).filter((edge) => !edge.targetPair);
  const keys = new Set<string>();
  for (const mode of ['relations', 'composition'] as const)
    for (const edge of artifactEdges(mode === 'relations' ? relations : [], composition, ids, mode))
      if (edge.from !== edge.to && ids.includes(edge.from) && ids.includes(edge.to)) keys.add([edge.from, edge.to].sort().join('\u0000'));
  return [...keys].map((key) => key.split('\u0000')).map(([from, to]) => ({ from, to }));
}

function artifactsLayout(model: ExplorerModel, options: ViewOptions): Layout {
  const artifacts = visibleArtifacts(model, options);
  const ids = artifacts.map((a) => a.id);
  const positions = connectedLayout(ids, everyRolledPair(model, ids));
  const cards: PlacedCard[] = artifacts.map((entity) => {
    const p = positions.get(entity.id)!;
    return {
      id: entity.id,
      entity,
      kind: 'artifact',
      scopeId: 'scope:artifacts',
      x: p.x,
      y: p.y,
      w: CONNECTED_CARD_W,
      h: CONNECTED_CARD_H,
    };
  });
  const boundaries: Boundary[] = [
    placedToHold({ id: 'scope:artifacts', title: 'Artifacts', caption: '', role: 'section' as const, scopeId: '' }, cards),
  ];
  return drawingOnlyWhatSomethingDeclares(cards, boundaries, []);
}

function elementsLayout(model: ExplorerModel, options: ViewOptions): Layout {
  const cards: PlacedCard[] = [];
  const boundaries: Boundary[] = [];
  const artifacts = visibleArtifacts(model, options);
  const artifactCards: PlacedCard[] = artifacts.map((entity, index) => ({
    id: entity.id,
    entity,
    kind: 'artifact',
    scopeId: 'scope:artifacts',
    x: ARTIFACTS_X + ARTIFACT_CARD_X + (index % ARTIFACT_COLUMNS) * ARTIFACT_STEP_X,
    y: ARTIFACTS_Y + ARTIFACT_CARD_Y + Math.floor(index / ARTIFACT_COLUMNS) * ARTIFACT_STEP_Y,
    w: CARD_W,
    h: CARD_H,
  }));
  const artifactsBox: Boundary = sizedToHold(
    {
      id: 'scope:artifacts',
      title: 'Artifacts',
      caption: '',
      role: 'section' as const,
      scopeId: '',
      x: ARTIFACTS_X,
      y: ARTIFACTS_Y,
      w: ARTIFACTS_W,
      h: ARTIFACTS_H,
    },
    artifactCards,
  );
  boundaries.push(artifactsBox);
  cards.push(...artifactCards);

  const elements = visibleElements(model, options);
  const elementsTop =
    artifactsBox.y +
    artifactsBox.h +
    (ELEMENTS_Y - ARTIFACTS_Y - artifactsBox.h > 0 ? ELEMENTS_Y - artifactsBox.y - artifactsBox.h : PHASE_Y);
  if (!options.group) {
    const flatCards: PlacedCard[] = elements.map((entity, index) => ({
      id: entity.id,
      entity,
      kind: 'element',
      scopeId: 'scope:elements',
      x: FLAT_X + (index % FLAT_COLUMNS) * FLAT_STEP_X,
      y: elementsTop + FLAT_Y + Math.floor(index / FLAT_COLUMNS) * FLAT_STEP_Y,
      w: CARD_W,
      h: CARD_H,
    }));
    boundaries.push(
      sizedToHold(
        {
          id: 'scope:elements',
          title: 'Elements',
          caption: '',
          role: 'section' as const,
          scopeId: '',
          x: ELEMENTS_X,
          y: elementsTop,
          w: ELEMENTS_W,
          h: ELEMENTS_H,
        },
        flatCards,
      ),
    );
    cards.push(...flatCards);
    return drawingOnlyWhatSomethingDeclares(cards, boundaries, []);
  }

  const ordering = model.orderingFrameId.split(':').slice(1).join(':');
  const options_ = orderingOptions(model);
  const groups = options_
    .map((option) => ({
      option,
      members: elements.filter((e) => (e.frameValues[ordering] ?? e.raw[ordering]) === option.sourceId),
    }))
    .filter((group) => group.members.length);
  const groupBoxes: Boundary[] = [];
  groups.forEach((group, index) => {
    const x = PHASE_X + (index % PHASE_COLUMNS) * PHASE_STEP_X;
    const y = elementsTop + PHASE_Y + Math.floor(index / PHASE_COLUMNS) * PHASE_STEP_Y;
    const members: PlacedCard[] = group.members.map((entity, member) => ({
      id: entity.id,
      entity,
      kind: 'element',
      scopeId: group.option.id,
      x: x + PHASE_CARD_X + (member % PHASE_CARD_COLUMNS) * PHASE_CARD_STEP_X,
      y: y + PHASE_CARD_Y + Math.floor(member / PHASE_CARD_COLUMNS) * PHASE_CARD_STEP_Y,
      w: CARD_W,
      h: CARD_H,
    }));
    const head = { title: group.option.label, caption: group.option.description, x, y };
    groupBoxes.push({ id: group.option.id, role: 'group', scopeId: 'scope:elements', ...head, ...sizeHolding(head, members) });
    cards.push(...members);
  });
  boundaries.push(
    sizedToHold(
      {
        id: 'scope:elements',
        title: 'Elements',
        caption: '',
        role: 'section' as const,
        scopeId: '',
        x: ELEMENTS_X,
        y: elementsTop,
        w: ELEMENTS_W,
        h: ELEMENTS_H,
      },
      groupBoxes,
    ),
    ...groupBoxes,
  );
  return drawingOnlyWhatSomethingDeclares(cards, boundaries, []);
}

export function layoutFor(model: ExplorerModel, options: ViewOptions): Layout {
  if (options.view === 'frames') return framesLayout(model);
  if (options.view === 'artifacts') return artifactsLayout(model, options);
  return elementsLayout(model, options);
}

const TITLE_RISE = 20;
const TITLE_DROP = 22;
const CAPTION_DROP = 56;
const HEAD_INSET = 21;
const TITLE_GLYPH = 30;
const TITLE_CHAR = 16.5;
const CAPTION_CHAR = 8.2;

function headingWidth(head: { title: string; caption: string }): number {
  return HEAD_INSET + Math.max(TITLE_GLYPH + head.title.length * TITLE_CHAR, head.caption.length * CAPTION_CHAR);
}

export const boundaryHeads = (layout: Layout): Rect[] =>
  layout.boundaries.map((b) => ({
    x: b.x,
    y: b.y - TITLE_RISE,
    w: Math.min(b.w, headingWidth(b)),
    h: TITLE_RISE + (b.caption ? CAPTION_DROP : TITLE_DROP),
  }));

export const cardRects = (layout: Layout) => new Map(layout.cards.map((c) => [c.id, { x: c.x, y: c.y, w: c.w, h: c.h }]));
