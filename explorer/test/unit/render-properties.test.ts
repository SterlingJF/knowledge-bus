import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { type Point, type Rect, intersects, union } from '@/src/lib/geometry';
import {
  LEGEND_ROWS,
  LEGEND_ROW_HOLDING,
  type LegendRow,
  type Scene,
  type SceneEdge,
  buildScene,
  holdingDrawn,
  legendRows,
} from '@/src/lib/scene';
import { type Holding } from '@/src/lib/composition-grouping';
import { type Boundary, type Layout, boundaryHeads, layoutFor, roleOfTheBoundaryEachCardStandsIn } from '@/src/lib/layout';
import { connectedLayout } from '@/src/lib/connected-layout';
import { type ExplorerModel, type Entity, type ViewOptions, emptySelection, initialOptions, updateOptions } from '@/src/lib/model';
import { buildFresh, everyState, geometryStates, labelStates, model, routeStates, sceneFor, type RenderState } from './render-states';

const cardRect = (c: { x: number; y: number; w: number; h: number }): Rect => ({ x: c.x, y: c.y, w: c.w, h: c.h });
const cardsOf = (scene: Scene) => scene.layout.cards.map(cardRect);
const labelBoxes = (scene: Scene) => scene.labels.map((l) => l.box);

const crossingsOfTheSameEdges = new WeakMap<SceneEdge[], Point[]>();

function crossings(edges: SceneEdge[]): Point[] {
  const seen = crossingsOfTheSameEdges.get(edges);
  if (seen) return seen;
  const drawn = edges.filter((e) => e.drawn && e.points.length > 1);
  const segments = drawn.map((e) => e.points.slice(1).map((p, i) => ({ a: e.points[i], b: p })));
  const meeting = (s: { a: Point; b: Point }, t: { a: Point; b: Point }): Point | null => {
    const sH = s.a.y === s.b.y;
    const tH = t.a.y === t.b.y;
    if (sH === tH) return null;
    const h = sH ? s : t;
    const v = sH ? t : s;
    const within = (p: number, q: number, value: number) => value >= Math.min(p, q) && value <= Math.max(p, q);
    return within(h.a.x, h.b.x, v.a.x) && within(v.a.y, v.b.y, h.a.y) ? { x: v.a.x, y: h.a.y } : null;
  };
  const found: Point[] = [];
  for (let i = 0; i < segments.length; i += 1)
    for (let j = i + 1; j < segments.length; j += 1)
      for (const s of segments[i])
        for (const t of segments[j]) {
          const p = meeting(s, t);
          if (p) found.push(p);
        }
  crossingsOfTheSameEdges.set(edges, found);
  return found;
}

const each = (states: RenderState[], name: string, check: (scene: Scene, state: RenderState) => string | null) =>
  test(name, () => {
    const failures = states
      .map((state) => ({ state, note: check(sceneFor(state), state) }))
      .filter((r) => r.note)
      .map((r) => `${r.state.name}: ${r.note}`);
    assert.deepEqual(failures, []);
  });

const encloses = (outer: Rect, inner: Rect) =>
  inner.x >= outer.x && inner.y >= outer.y && inner.x + inner.w <= outer.x + outer.w && inner.y + inner.h <= outer.y + outer.h;

const cardOutsideItsOwner = (layout: Layout): string | null => {
  for (const card of layout.cards) {
    const owner = layout.boundaries.find((b) => b.id === card.scopeId);
    if (!owner) return `${card.id} claims ${card.scopeId}, which this layout does not draw`;
    if (!encloses(owner, cardRect(card))) return `${card.id} is drawn outside ${owner.id}`;
  }
  return null;
};

export interface BoundaryGaps {
  beside: number;
  below: number;
}

const boundariesSomethingDeclares = (layout: Layout): Set<string> => {
  const declared = new Set([...layout.cards.map((c) => c.scopeId), ...layout.notes.map((n) => n.scopeId)]);
  for (let growing = true; growing;) {
    growing = false;
    for (const boundary of layout.boundaries)
      if (declared.has(boundary.id) && boundary.scopeId && !declared.has(boundary.scopeId)) {
        declared.add(boundary.scopeId);
        growing = true;
      }
  }
  return declared;
};

const whatDeclares = (layout: Layout, id: string, declared: Set<string>): Rect[] => [
  ...layout.cards.filter((c) => c.scopeId === id).map(cardRect),
  ...layout.notes.filter((n) => n.scopeId === id).map(cardRect),
  ...layout.boundaries.filter((b) => b.scopeId === id && declared.has(b.id)).map(cardRect),
];

export const boundaryNotSizedFromWhatDeclaresIt = (layout: Layout, gaps: BoundaryGaps): string | null => {
  const declared = boundariesSomethingDeclares(layout);
  const heads = boundaryHeads(layout);
  for (const [index, boundary] of layout.boundaries.entries()) {
    if (!declared.has(boundary.id)) return `${boundary.id} is drawn but nothing declares it`;
    const inside = union(whatDeclares(layout, boundary.id, declared));
    const head = heads[index];
    const reach: [string, number, number][] = [
      ['left', inside.x - boundary.x, gaps.beside],
      ['top', inside.y - boundary.y, head.y + head.h - boundary.y + gaps.below],
      ['right', boundary.x + boundary.w - inside.x - inside.w, Math.max(gaps.beside, boundary.x + head.w - inside.x - inside.w)],
      ['bottom', boundary.y + boundary.h - inside.y - inside.h, gaps.below],
    ];
    const over = reach.find(([, taken, allowed]) => taken > allowed);
    if (over) return `${boundary.id} reaches ${over[1]} past what declares it on the ${over[0]} edge, where this layout allows ${over[2]}`;
  }
  return null;
};

type BoundaryRole = Boundary['role'];

const GROUND_TOKEN = '--kb-ground-frame';

const BOUNDARY_ROLES: readonly BoundaryRole[] = ['section', 'group', 'scope'];

const boundaryNamesAFrameOrOneOfItsValues = (role: BoundaryRole): boolean => role !== 'section';

const rolesTheStylesheetGivesTheGround = (css: string, token: string): Set<BoundaryRole> => {
  const drawing = new Set<BoundaryRole>();
  for (const rule of css.matchAll(/([^{}]+)\{([^{}]*)\}/g))
    if (rule[2].includes(`var(${token})`))
      for (const role of BOUNDARY_ROLES) if (rule[1].includes(`.boundary[data-role='${role}']`)) drawing.add(role);
  return drawing;
};

const rulesOf = (css: string) =>
  [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map((rule) => ({ selectors: rule[1].split(',').map((s) => s.trim()), body: rule[2] }));

const DIMMED_CARD = ".card[data-state='dimmed']";

const ownerRolesUnderWhichADimmedCardPaints = (css: string, token: string): Set<BoundaryRole> => {
  const painting = new Set<BoundaryRole>();
  for (const rule of rulesOf(css))
    if (/(?:^|;)\s*background:/.test(rule.body) && rule.body.includes(`var(${token})`))
      for (const role of BOUNDARY_ROLES) if (rule.selectors.includes(`${DIMMED_CARD}[data-owner-role='${role}']`)) painting.add(role);
  return painting;
};

const whatADimmedCardPaintsUnderNoOtherRule = (css: string): string[] =>
  rulesOf(css)
    .filter((rule) => rule.selectors.includes(DIMMED_CARD))
    .flatMap((rule) => [...rule.body.matchAll(/(?:^|;)\s*background:\s*([^;]+);/g)].map((found) => found[1].trim()));

export const cardWhoseOwnerDoesNotSettleTheGroundItStandsOn = (
  layout: Layout,
  drawing: Set<BoundaryRole>,
  declaredRoles: Map<string, BoundaryRole> = roleOfTheBoundaryEachCardStandsIn(layout),
): string | null => {
  const byId = new Map(layout.boundaries.map((boundary) => [boundary.id, boundary]));
  for (const card of layout.cards) {
    const owner = byId.get(card.scopeId);
    if (!owner) return `${card.id} declares ${card.scopeId || 'no boundary'}, which this layout does not draw`;
    if (declaredRoles.get(card.id) !== owner.role)
      return `${card.id} stands in ${owner.id}, a ${owner.role}, and is told ${declaredRoles.get(card.id)}`;
    if (drawing.has(owner.role)) continue;
    const walked = new Set([owner.id]);
    for (let outer = byId.get(owner.scopeId); outer && !walked.has(outer.id); outer = byId.get(outer.scopeId)) {
      if (drawing.has(outer.role))
        return `${card.id} stands in ${owner.id}, which draws no ground, inside ${outer.id}, which does, so its owner's role does not say what ground is under it`;
      walked.add(outer.id);
    }
  }
  return null;
};

export const groundDrawnWhereTheFrameRuleDoesNotPutIt = (layout: Layout, drawing: Set<BoundaryRole>): string | null => {
  const carries = (boundary: Boundary) => drawing.has(boundary.role);
  for (const boundary of layout.boundaries) {
    if (boundaryNamesAFrameOrOneOfItsValues(boundary.role) && !carries(boundary))
      return `${boundary.id} names a frame or one of its values as a ${boundary.role} and draws no ground`;
    if (!boundaryNamesAFrameOrOneOfItsValues(boundary.role) && carries(boundary))
      return `${boundary.id} is a ${boundary.role} and draws the ground anyway`;
  }
  const byId = new Map(layout.boundaries.map((boundary) => [boundary.id, boundary]));
  for (const boundary of layout.boundaries.filter(carries)) {
    const walked = new Set([boundary.id]);
    for (let owner = byId.get(boundary.scopeId); owner && !walked.has(owner.id); owner = byId.get(owner.scopeId)) {
      if (carries(owner)) return `${boundary.id} draws the ground inside ${owner.id}, which declares it and draws the ground too`;
      walked.add(owner.id);
    }
  }
  return null;
};

const patternsCss = readFileSync(new URL('../../styles/patterns.css', import.meta.url), 'utf8');

const groundedRoles = rolesTheStylesheetGivesTheGround(patternsCss, GROUND_TOKEN);

const drawnEdgeTheSwatchDescribes: Record<LegendRow, (edge: SceneEdge) => boolean> = {
  direct: (edge) => edge.paint === 'element',
  rolled: (edge) => edge.paint === 'rolled',
  required: (edge) => edge.grade === 'required',
  situational: (edge) => edge.grade === 'situational',
  mixed: (edge) => edge.grade === 'mixed',
  owns: (edge) => holdingDrawn(edge) === 'owns',
  links: (edge) => holdingDrawn(edge) === 'links',
};

const legendRowDescribingNothingDrawn = (rows: readonly LegendRow[], scene: Scene): string | null => {
  const drawn = scene.edges.filter((e) => e.drawn);
  const unmatched = rows.filter((row) => !drawn.some(drawnEdgeTheSwatchDescribes[row]));
  return unmatched.length ? `legend row ${unmatched.join(' and ')} describes nothing this scene draws` : null;
};

type DrawnMark =
  | `paint:${SceneEdge['paint']}`
  | `dash:${Exclude<SceneEdge['dash'], 'none'>}`
  | `grade:${NonNullable<SceneEdge['grade']>}`
  | `holding:${Holding}`;

const NO_ROW_DESCRIBES_IT = 'no row describes it';

const rowExplainingDrawnMark: Record<DrawnMark, LegendRow | typeof NO_ROW_DESCRIBES_IT> = {
  'paint:element': 'direct',
  'paint:rolled': 'rolled',
  'paint:frame': NO_ROW_DESCRIBES_IT,
  'dash:situational': 'situational',
  'dash:mixed': 'mixed',
  'dash:frame': NO_ROW_DESCRIBES_IT,
  'grade:required': 'required',
  'grade:situational': 'situational',
  'grade:mixed': 'mixed',
  'holding:owns': 'owns',
  'holding:links': 'links',
};

const marksADrawnEdgeShows = (edge: SceneEdge): DrawnMark[] => {
  const holding = holdingDrawn(edge);
  return [
    `paint:${edge.paint}` as DrawnMark,
    ...(edge.dash === 'none' ? [] : ([`dash:${edge.dash}`] as DrawnMark[])),
    ...(edge.grade ? ([`grade:${edge.grade}`] as DrawnMark[]) : []),
    ...(holding ? ([`holding:${holding}`] as DrawnMark[]) : []),
  ];
};

const drawnMarkNoMountedRowExplains = (rows: readonly LegendRow[], scene: Scene): string | null => {
  for (const edge of scene.edges.filter((e) => e.drawn))
    for (const mark of marksADrawnEdgeShows(edge)) {
      const row = rowExplainingDrawnMark[mark];
      if (row === NO_ROW_DESCRIBES_IT) return `${edge.path} draws ${mark}, and ${NO_ROW_DESCRIBES_IT}`;
      if (!rows.includes(row)) return `${edge.path} draws ${mark}, which the mounted legend leaves unexplained`;
    }
  return null;
};

const firstStateWhere = (matches: (scene: Scene) => boolean): RenderState => everyState().find((state) => matches(sceneFor(state)))!;

test('a legend row accepted on a scene that draws its paint is reported once those edges are gone', () => {
  const onlyRolled = firstStateWhere((s) => s.edges.some((e) => e.drawn) && s.edges.every((e) => !e.drawn || e.paint === 'rolled'));
  const scene = sceneFor(onlyRolled);
  assert.equal(legendRowDescribingNothingDrawn(['rolled'], scene), null, `${onlyRolled.name} draws rolled edges, so the row is matched`);
  const stripped: Scene = { ...scene, edges: scene.edges.filter((e) => e.paint !== 'rolled') };
  assert.equal(legendRowDescribingNothingDrawn(['rolled'], stripped), 'legend row rolled describes nothing this scene draws');
});

test('legend rows whose edges the scene holds but does not draw are reported', () => {
  const nothingDrawn = firstStateWhere((s) => s.edges.length > 0 && s.edges.every((e) => !e.drawn));
  const scene = sceneFor(nothingDrawn);
  assert.ok(scene.edges.length > 0, `${nothingDrawn.name} must carry edges, so the report cannot come from an empty scene`);
  assert.equal(
    legendRowDescribingNothingDrawn(['direct', 'rolled'], scene),
    'legend row direct and rolled describes nothing this scene draws',
  );
});

test('a drawn edge carrying a paint no row can describe is reported even when the legend mounts every row', () => {
  const drawsElements = firstStateWhere((s) => s.edges.some((e) => e.drawn && e.paint === 'element'));
  const scene = sceneFor(drawsElements);
  assert.equal(
    drawnMarkNoMountedRowExplains(legendRows(scene), scene),
    null,
    `${drawsElements.name} draws only marks the rows it mounts describe`,
  );
  const framed: Scene = { ...scene, edges: scene.edges.map((e) => (e.drawn ? { ...e, paint: 'frame' as const } : e)) };
  assert.equal(
    drawnMarkNoMountedRowExplains(LEGEND_ROWS, framed),
    `${framed.edges.find((e) => e.drawn)!.path} draws paint:frame, and ${NO_ROW_DESCRIBES_IT}`,
  );
});

interface Swatch {
  hue: string;
  dash: string;
  hidden: boolean;
}

const BLANK_SWATCH: Swatch = { hue: '', dash: '', hidden: false };

const HUE_PROPERTIES = ['border-top-color', 'border-color', 'stroke', 'color'];
const DASH_PROPERTIES = ['border-top-style', 'border-style', 'stroke-dasharray'];
const SHORTHAND_PARTS = 3;

const declarationsOf = (block: string): [string, string][] =>
  block
    .split(';')
    .map((line) => line.split(/:(.*)/s))
    .filter((parts) => parts.length > 1)
    .map(([name, value]) => [name.trim(), value.trim()] as [string, string]);

const applied = (swatch: Swatch, block: string): Swatch => {
  let next = swatch;
  for (const [name, value] of declarationsOf(block)) {
    const parts = value.split(/\s+/);
    if (name === 'border-top' && parts.length === SHORTHAND_PARTS) next = { ...next, dash: parts[1], hue: parts[2] };
    if (HUE_PROPERTIES.includes(name)) next = { ...next, hue: value };
    if (DASH_PROPERTIES.includes(name)) next = { ...next, dash: value };
    if (name === 'display') next = { ...next, hidden: value === 'none' };
  }
  return next;
};

const KEYED = /\[data-key='([\w-]+)'\]/g;

const swatchEachLegendRowDraws = (css: string, rows: readonly LegendRow[]): Map<LegendRow, Swatch> => {
  const drawn = new Map<LegendRow, Swatch>(rows.map((row) => [row, BLANK_SWATCH]));
  for (const rule of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const selector = rule[1];
    if (!selector.includes('.legend')) continue;
    const keyed = [...selector.matchAll(KEYED)].map(([, key]) => key);
    const targets = keyed.length ? rows.filter((row) => keyed.includes(row)) : rows;
    for (const row of targets) drawn.set(row, applied(drawn.get(row)!, rule[2]));
  }
  return drawn;
};

test('no two legend rows draw the same mark: a hue row differs in hue, a pattern row in pattern, a holding row in its glyph', () => {
  const swatches = swatchEachLegendRowDraws(patternsCss, LEGEND_ROWS);
  const markOf = (row: LegendRow): string => {
    const holding = LEGEND_ROW_HOLDING[row];
    if (holding) return `glyph:${holding}`;
    const swatch = swatches.get(row)!;
    return swatch.hidden ? 'nothing at all' : `hue ${swatch.hue || 'unset'} drawn ${swatch.dash || 'unset'}`;
  };
  const collisions: string[] = [];
  for (const [index, row] of LEGEND_ROWS.entries())
    for (const other of LEGEND_ROWS.slice(index + 1))
      if (markOf(row) === markOf(other)) collisions.push(`${row} and ${other} both draw ${markOf(row)}`);
  assert.deepEqual(collisions, []);
});

const groupedElements = () => layoutFor(model, updateOptions(initialOptions(), { view: 'elements', group: true }));
const framesLayout = () => layoutFor(model, updateOptions(initialOptions(), { view: 'frames' }));

const cardsDeclaring = (layout: Layout, id: string) => layout.cards.filter((c) => c.scopeId === id).map(cardRect);

const columnsFilled = (cards: Rect[]): number => new Set(cards.map((c) => c.x)).size;

const theGroupWhoseCardsFillTheMostColumns = (layout: Layout): Boundary =>
  layout.boundaries
    .filter((b) => b.role === 'group')
    .reduce((widest, b) => (columnsFilled(cardsDeclaring(layout, b.id)) > columnsFilled(cardsDeclaring(layout, widest.id)) ? b : widest));

const gapsTheLayoutAlreadyLeaves = (layout: Layout): BoundaryGaps => {
  const group = theGroupWhoseCardsFillTheMostColumns(layout);
  const claimed = union(cardsDeclaring(layout, group.id));
  return { beside: group.x + group.w - (claimed.x + claimed.w), below: group.y + group.h - (claimed.y + claimed.h) };
};

const gapsEveryBoundaryGets = gapsTheLayoutAlreadyLeaves(groupedElements());

test('a boundary grown past the gap its own layout leaves beside a card is reported', () => {
  const layout = groupedElements();
  assert.equal(
    boundaryNotSizedFromWhatDeclaresIt(layout, gapsEveryBoundaryGets),
    null,
    'the layout the gaps are read from must itself satisfy them',
  );
  const target = theGroupWhoseCardsFillTheMostColumns(layout);
  const grown = { ...layout, boundaries: layout.boundaries.map((b) => (b.id === target.id ? { ...b, w: b.w + 1 } : b)) };
  assert.equal(
    boundaryNotSizedFromWhatDeclaresIt(grown, gapsEveryBoundaryGets),
    `${target.id} reaches ${gapsEveryBoundaryGets.beside + 1} past what declares it on the right edge, where this layout allows ${gapsEveryBoundaryGets.beside}`,
  );
});

test('a boundary wide enough only because it draws a long caption is accepted, and one pixel wider is not', () => {
  const layout = groupedElements();
  const captioned = layout.boundaries.filter((b) => b.role === 'group');
  const index = captioned
    .map((b) => layout.boundaries.indexOf(b))
    .find((i) => {
      const claimed = union(cardsDeclaring(layout, layout.boundaries[i].id));
      return layout.boundaries[i].x + layout.boundaries[i].w - claimed.x - claimed.w > gapsEveryBoundaryGets.beside;
    })!;
  const wider = layout.boundaries[index];
  assert.ok(wider.caption.length > 0, `${wider.id} must be wider than its cards because of a caption for this case to mean anything`);
  assert.equal(boundaryNotSizedFromWhatDeclaresIt(layout, gapsEveryBoundaryGets), null, 'a boundary drawn to fit its heading is accepted');
  const grown = { ...layout, boundaries: layout.boundaries.map((b) => (b.id === wider.id ? { ...b, w: b.w + 1 } : b)) };
  const allowed =
    boundaryHeads(layout)[index].w - union(cardsDeclaring(layout, wider.id)).w - (union(cardsDeclaring(layout, wider.id)).x - wider.x);
  assert.equal(
    boundaryNotSizedFromWhatDeclaresIt(grown, gapsEveryBoundaryGets),
    `${wider.id} reaches ${allowed + 1} past what declares it on the right edge, where this layout allows ${allowed}`,
  );
});

test('a boundary lifted higher than the drop its own heading takes is reported', () => {
  const layout = groupedElements();
  const index = layout.boundaries.findIndex((b) => b.role === 'group');
  const group = layout.boundaries[index];
  const head = boundaryHeads(layout)[index];
  const allowed = head.y + head.h - group.y + gapsEveryBoundaryGets.below;
  const top = union(cardsDeclaring(layout, group.id)).y - allowed - 1;
  const lifted = { ...layout, boundaries: layout.boundaries.map((b) => (b.id === group.id ? { ...b, y: top, h: b.h + (b.y - top) } : b)) };
  assert.equal(
    boundaryNotSizedFromWhatDeclaresIt(lifted, gapsEveryBoundaryGets),
    `${group.id} reaches ${allowed + 1} past what declares it on the top edge, where this layout allows ${allowed}`,
  );
});

test('a section is declared by the boundaries nested inside it, and a boundary nothing declares is reported', () => {
  const layout = groupedElements();
  const elements = layout.boundaries.find((b) => b.id === 'scope:elements')!;
  assert.equal(cardsDeclaring(layout, elements.id).length, 0, 'no card declares the elements section, so only nesting can declare it');
  assert.ok(
    layout.boundaries.some((b) => b.scopeId === elements.id),
    'the elements section must hold nested boundaries for this case to be able to pass',
  );
  assert.equal(
    boundaryNotSizedFromWhatDeclaresIt(layout, gapsEveryBoundaryGets),
    null,
    'a section its nested boundaries declare is accepted',
  );
  const unnested = { ...layout, boundaries: layout.boundaries.map((b) => (b.scopeId === elements.id ? { ...b, scopeId: '' } : b)) };
  assert.equal(boundaryNotSizedFromWhatDeclaresIt(unnested, gapsEveryBoundaryGets), 'scope:elements is drawn but nothing declares it');
});

test('a boundary drawn around nothing is reported, and the frames view draws none', () => {
  const frames = framesLayout();
  assert.equal(
    boundaryNotSizedFromWhatDeclaresIt(frames, gapsEveryBoundaryGets),
    null,
    'every boundary the frames view draws holds something',
  );
  const aroundNothing: Boundary = { ...frames.boundaries[0], id: 'scope:nothing-holds-this' };
  assert.equal(
    boundaryNotSizedFromWhatDeclaresIt({ ...frames, boundaries: [...frames.boundaries, aroundNothing] }, gapsEveryBoundaryGets),
    'scope:nothing-holds-this is drawn but nothing declares it',
  );
});

test('a card drawn outside the boundary that claims it is an escape, even when another boundary still contains it', () => {
  const layout = groupedElements();
  const elements = layout.boundaries.find((b) => b.id === 'scope:elements')!;
  const group = layout.boundaries.find((b) => b.role === 'group')!;
  const card = layout.cards.find((c) => encloses(group, cardRect(c)))!;
  const moved = { ...card, x: elements.x + 2, y: elements.y + elements.h - card.h - 2 };
  assert.ok(encloses(elements, cardRect(moved)), 'the moved card must still sit inside the elements section');
  assert.equal(
    cardOutsideItsOwner({ ...layout, cards: layout.cards.map((c) => (c.id === card.id ? moved : c)) }),
    `${card.id} is drawn outside ${group.id}`,
  );
});

const grownTo = (kind: 'artifact' | 'element', total: number): ExplorerModel => {
  const present = model.entities.filter((e) => e.kind === kind).length;
  const added = Array.from({ length: total - present }, (_, index) => ({
    id: `${kind}:synthetic-${index + 1}`,
    label: `Synthetic ${kind} ${index + 1}`,
    kind,
    raw: {},
    frameValues: {},
  })) as Entity[];
  return { ...model, entities: [...model.entities, ...added] };
};

const outgrowsTheConstantBox: { name: string; kind: 'artifact' | 'element'; total: number; patch: Partial<ViewOptions> }[] = [
  { name: 'a 21st artifact in the artifacts view', kind: 'artifact', total: 21, patch: { view: 'artifacts' } },
  { name: 'a 28th artifact in the elements view', kind: 'artifact', total: 28, patch: { view: 'elements', group: false } },
  { name: 'a 109th element in the flat elements view', kind: 'element', total: 109, patch: { view: 'elements', group: false } },
];

test('a universe one entity past what a constant-sized boundary held still draws every card inside its own boundary', () => {
  for (const state of outgrowsTheConstantBox) {
    const layout = layoutFor(grownTo(state.kind, state.total), updateOptions(initialOptions(), state.patch));
    const drawn = layout.cards.filter((c) => c.kind === state.kind).length;
    assert.equal(drawn, state.total, `${state.name}: the synthetic entities must reach the layout for this case to be able to fail`);
    assert.equal(cardOutsideItsOwner(layout), null, state.name);
  }
});

each(geometryStates(), 'P1 no card overlaps another, and every card sits inside the boundary that claims it', (scene) => {
  const cards = scene.layout.cards;
  for (let i = 0; i < cards.length; i += 1)
    for (let j = i + 1; j < cards.length; j += 1)
      if (intersects(cardRect(cards[i]), cardRect(cards[j]))) return `${cards[i].id} overlaps ${cards[j].id}`;
  return cardOutsideItsOwner(scene.layout);
});

each(routeStates(), 'P2 every drawn route segment is axis aligned', (scene) => {
  for (const edge of scene.edges.filter((e) => e.drawn))
    for (let i = 1; i < edge.points.length; i += 1) {
      const a = edge.points[i - 1];
      const b = edge.points[i];
      if (a.x !== b.x && a.y !== b.y) return `${edge.path} has a diagonal segment`;
    }
  return null;
});

each(routeStates(), 'P3 no drawn route passes through a card', (scene) => {
  const cards = cardsOf(scene);
  for (const edge of scene.edges.filter((e) => e.drawn))
    for (let i = 1; i < edge.points.length; i += 1) {
      const a = edge.points[i - 1];
      const b = edge.points[i];
      const seg = { x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), w: Math.abs(a.x - b.x) || 1, h: Math.abs(a.y - b.y) || 1 };
      const inside = cards.find((c) => intersects({ ...seg, x: seg.x + 1, y: seg.y + 1, w: seg.w - 2, h: seg.h - 2 }, c));
      if (inside) return `${edge.path} crosses a card at ${seg.x},${seg.y}`;
    }
  return null;
});

each(labelStates(), 'P4 no label box contains an intersection of two drawn routes', (scene) => {
  const points = crossings(scene.edges);
  for (const label of scene.labels) {
    const hit = points.find(
      (p) => p.x >= label.box.x && p.x <= label.box.x + label.box.w && p.y >= label.box.y && p.y <= label.box.y + label.box.h,
    );
    if (hit) return `label "${label.text}" on ${label.edge} covers a crossing at ${hit.x},${hit.y}`;
  }
  return null;
});

each(labelStates(), 'P5 no label box overlaps a card, a boundary heading, or another label', (scene) => {
  const cards = [...cardsOf(scene), ...boundaryHeads(scene.layout)];
  const boxes = labelBoxes(scene);
  for (const [index, box] of boxes.entries()) {
    if (cards.some((c) => intersects(box, c))) return `label "${scene.labels[index].text}" overlaps a card or heading`;
    for (let j = index + 1; j < boxes.length; j += 1)
      if (intersects(box, boxes[j])) return `labels "${scene.labels[index].text}" and "${scene.labels[j].text}" overlap`;
  }
  return null;
});

each(routeStates(), 'P6 every active drawn edge is identifiable, by a label or by its endpoint nubs', (scene, state) => {
  const active = scene.edges.filter((e) => e.drawn && (e.on || state.selection.connection === e.path));
  const labelled = new Set(scene.labels.map((l) => l.edge));
  const nubbed = new Set(scene.nubs.map((n) => n.id));
  const missing = active.filter((e) => !labelled.has(e.path) && !(nubbed.has(e.from) && nubbed.has(e.to)));
  return missing.length ? `${missing.length} active edges are unidentifiable, first ${missing[0].path}` : null;
});

each(
  geometryStates(),
  'P7 nubs dock to their own card, overlap no card, no boundary heading and no other nub, and stay inside their scope',
  (scene) => {
    const cards = new Map(scene.layout.cards.map((c) => [c.id, cardRect(c)]));
    const heads = boundaryHeads(scene.layout);
    const placed: Rect[] = [];
    for (const nub of scene.nubs) {
      const head = heads.findIndex((rect) => intersects(nub.box, rect));
      if (head >= 0) return `nub ${nub.id} overlaps the heading of ${scene.layout.boundaries[head].id}`;
      const own = cards.get(nub.id);
      if (!own) return `nub ${nub.id} has no card`;
      const onBoundary =
        (nub.from.x === own.x || nub.from.x === own.x + own.w || (nub.from.x >= own.x && nub.from.x <= own.x + own.w)) &&
        (nub.from.y === own.y || nub.from.y === own.y + own.h || (nub.from.y >= own.y && nub.from.y <= own.y + own.h));
      if (!onBoundary) return `nub ${nub.id} anchors away from its card`;
      for (const [id, rect] of cards)
        if (!nub.inset && id !== nub.id && intersects(nub.box, rect)) return `nub ${nub.id} overlaps card ${id}`;
      if (placed.some((r) => intersects(nub.box, r))) return `nub ${nub.id} overlaps another nub`;
      placed.push(nub.box);
    }
    return null;
  },
);

each(everyState(), 'P8 identical inputs produce an identical scene', (scene, state) => {
  const again = buildFresh(state);
  const shape = (s: Scene) => ({
    cards: s.layout.cards.map((c) => [c.id, c.x, c.y, c.w, c.h]),
    boundaries: s.layout.boundaries.map((b) => [b.id, b.x, b.y, b.w, b.h]),
    edges: s.edges.map((e) => [e.path, e.d, e.drawn, e.on, e.dash]),
    labels: s.labels.map((l) => [l.edge, l.text, l.box.x, l.box.y]),
    nubs: s.nubs.map((n) => [n.id, n.count, n.box.x, n.box.y, n.inset]),
  });
  return JSON.stringify(shape(scene)) === JSON.stringify(shape(again)) ? null : 'second build differs';
});

test('P9 the graph fed to card placement is every graph the view can draw', () => {
  const options = updateOptions(initialOptions(), { view: 'artifacts' });
  const ids = layoutFor(model, options).cards.map((c) => c.id);
  const keys = new Set<string>();
  for (const connections of ['relations', 'composition'] as const)
    for (const edge of buildScene(model, updateOptions(options, { connections }), emptySelection()).edges)
      if (edge.from !== edge.to && ids.includes(edge.from) && ids.includes(edge.to)) keys.add([edge.from, edge.to].sort().join('|'));
  const pairs = [...keys].map((k) => k.split('|')).map(([from, to]) => ({ from, to }));
  const expected = connectedLayout(ids, pairs);
  const actual = new Map(layoutFor(model, options).cards.map((c) => [c.id, { x: c.x, y: c.y }]));
  const wrong = ids.filter((id) => expected.get(id)!.x !== actual.get(id)!.x || expected.get(id)!.y !== actual.get(id)!.y);
  assert.deepEqual(wrong, [], `${wrong.length} of ${ids.length} artifacts are placed by a different graph than the one drawn`);
});

each(
  geometryStates(),
  'P10 every boundary is declared by a card or by a declared boundary nested inside it, and reaches no further past what declares it than the gaps the layout already leaves',
  (scene) => boundaryNotSizedFromWhatDeclaresIt(scene.layout, gapsEveryBoundaryGets),
);

each(everyState(), "P11 every drawn edge's paint and dash is described by a row the legend mounts", (scene) =>
  drawnMarkNoMountedRowExplains(legendRows(scene), scene),
);

test('the stylesheet gives the ground to the boundary roles that name a frame or one of its values, and to no other', () => {
  assert.deepEqual([...groundedRoles].sort(), BOUNDARY_ROLES.filter(boundaryNamesAFrameOrOneOfItsValues).sort());
});

test('a section handed the ground is reported, and so is a grounded boundary nested inside another', () => {
  const layout = groupedElements();
  const frameRoles = new Set<BoundaryRole>(BOUNDARY_ROLES.filter(boundaryNamesAFrameOrOneOfItsValues));
  assert.equal(
    groundDrawnWhereTheFrameRuleDoesNotPutIt(layout, frameRoles),
    null,
    'the shipped layout puts the ground where the rule does',
  );
  const section = layout.boundaries.find((b) => !boundaryNamesAFrameOrOneOfItsValues(b.role))!;
  assert.equal(
    groundDrawnWhereTheFrameRuleDoesNotPutIt(layout, new Set(BOUNDARY_ROLES)),
    `${section.id} is a ${section.role} and draws the ground anyway`,
  );
  const nested = { ...layout, boundaries: layout.boundaries.map((b) => (b.role === 'section' ? { ...b, role: 'scope' as const } : b)) };
  const inner = nested.boundaries.find((b) => b.role === 'group')!;
  assert.ok(
    nested.boundaries.some((b) => b.id === inner.scopeId),
    'the nested case needs a group whose declared scope this layout also draws',
  );
  assert.equal(
    groundDrawnWhereTheFrameRuleDoesNotPutIt(nested, frameRoles),
    `${inner.id} draws the ground inside ${inner.scopeId}, which declares it and draws the ground too`,
  );
});

each(
  geometryStates(),
  'P12 the ground is drawn by every boundary that names a frame or one of its values, by no section, and by no boundary nested inside another that draws it',
  (scene) => groundDrawnWhereTheFrameRuleDoesNotPutIt(scene.layout, groundedRoles),
);

test('the stylesheet has a dimmed card paint the ground under exactly the owner roles that draw it, and the canvas under every other', () => {
  assert.deepEqual([...ownerRolesUnderWhichADimmedCardPaints(patternsCss, GROUND_TOKEN)].sort(), [...groundedRoles].sort());
  assert.deepEqual(whatADimmedCardPaintsUnderNoOtherRule(patternsCss), ['var(--kb-canvas)']);
});

test('a card whose owner is not drawn is reported, and so are one told the wrong role and one standing in a section nested inside a boundary that draws the ground', () => {
  const layout = groupedElements();
  assert.equal(cardWhoseOwnerDoesNotSettleTheGroundItStandsOn(layout, groundedRoles), null, 'the shipped layout settles every card');
  const grouped = layout.cards.find((card) => layout.boundaries.some((b) => b.id === card.scopeId && b.role === 'group'))!;
  const orphaned = { ...layout, cards: layout.cards.map((card) => (card === grouped ? { ...card, scopeId: 'scope:nowhere' } : card)) };
  assert.equal(
    cardWhoseOwnerDoesNotSettleTheGroundItStandsOn(orphaned, groundedRoles),
    `${grouped.id} declares scope:nowhere, which this layout does not draw`,
  );
  const owner = layout.boundaries.find((b) => b.id === grouped.scopeId)!;
  assert.equal(
    cardWhoseOwnerDoesNotSettleTheGroundItStandsOn(
      layout,
      groundedRoles,
      new Map(roleOfTheBoundaryEachCardStandsIn(layout)).set(grouped.id, 'section'),
    ),
    `${grouped.id} stands in ${owner.id}, a ${owner.role}, and is told section`,
  );
  const swapped = {
    ...layout,
    boundaries: layout.boundaries.map((b) => ({ ...b, role: b.role === 'group' ? ('section' as const) : ('scope' as const) })),
  };
  const outer = swapped.boundaries.find((b) => b.id === layout.boundaries.find((g) => g.id === grouped.scopeId)!.scopeId)!;
  assert.equal(outer.role, 'scope', 'the nested case needs the section that holds the groups to draw the ground');
  const reported = cardWhoseOwnerDoesNotSettleTheGroundItStandsOn(swapped, groundedRoles) ?? '';
  assert.match(reported, new RegExp(`inside ${outer.id}, which does`));
});

each(
  geometryStates(),
  'every card stands in a boundary the layout draws, whose role alone says whether a ground is under the card',
  (scene) => cardWhoseOwnerDoesNotSettleTheGroundItStandsOn(scene.layout, groundedRoles),
);
