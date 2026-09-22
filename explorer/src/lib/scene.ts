import {
  type ExplorerModel,
  type ViewOptions,
  type Selection,
  type DisplayEdge,
  compositionEdges,
  compositionEntries,
  relationEdges,
  wiringEdges,
} from './model';
import { type Layout, layoutFor, boundaryHeads, cardRects } from './layout';
import { type Rect, type Point, polylineCrossings, union } from './geometry';
import { Router } from './routing';
import { artifactEdges, collapseCardPairs } from './rollup';
import { bundleExpandedPairs, bundleFocusCard } from './bundles';
import { placeLabels, sampleCount, type PlacedLabel, type LabelCandidate, type HorizontalRail } from './labels';
import { placeNubs, type PlacedNub } from './nubs';
import { type Holding, holdingOf } from './composition-grouping';

export interface SceneEdge extends DisplayEdge {
  drawn: boolean;
  d: string;
  points: Point[];
  on: boolean;
  emphasized: boolean;
  dash: 'none' | 'situational' | 'mixed' | 'frame';
  grade: 'required' | 'situational' | 'mixed' | null;
  paint: 'element' | 'rolled' | 'frame';
  midpoint: Point;
}

export const holdingDrawn = (edge: SceneEdge): Holding | null =>
  edge.paint === 'element' && edge.kind === 'composition' ? holdingOf(edge) : null;

export interface Scene {
  layout: Layout;
  edges: SceneEdge[];
  labelCandidates: LabelCandidate[];
  labels: PlacedLabel[];
  nubs: PlacedNub[];
  related: Set<string>;
  focus: string;
  bounds: Rect;
  zoom: number;
}

const MAX_DISPLAY_COUNT = 9;
const MIDPOINT = 0.5;

export type PathSampler = (d: string, count: number) => { samples: Point[]; middle: Point };

const straightSampler: PathSampler = (d, count) => {
  const numbers = (d.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
  const points: Point[] = [];
  for (let i = 0; i + 1 < numbers.length; i += 2) points.push({ x: numbers[i], y: numbers[i + 1] });
  const lengths = points.slice(1).map((p, i) => Math.hypot(p.x - points[i].x, p.y - points[i].y));
  const total = lengths.reduce((a, b) => a + b, 0) || 1;
  const at = (fraction: number): Point => {
    let remaining = fraction * total;
    for (let i = 0; i < lengths.length; i += 1) {
      if (remaining <= lengths[i] || i === lengths.length - 1) {
        const ratio = lengths[i] ? remaining / lengths[i] : 0;
        return { x: points[i].x + (points[i + 1].x - points[i].x) * ratio, y: points[i].y + (points[i + 1].y - points[i].y) * ratio };
      }
      remaining -= lengths[i];
    }
    return points[points.length - 1] ?? { x: 0, y: 0 };
  };
  return { samples: Array.from({ length: count }, (_, i) => at((i + 1) / (count + 1))), middle: at(MIDPOINT) };
};

function pathPoints(d: string): Point[] {
  const numbers = (d.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
  const points: Point[] = [];
  for (let i = 0; i + 1 < numbers.length; i += 2) points.push({ x: numbers[i], y: numbers[i + 1] });
  return points;
}

function baseEdges(model: ExplorerModel, options: ViewOptions): DisplayEdge[] {
  if (options.view === 'frames') return [];
  if (!options.connections) return [];
  const source = options.connections === 'composition' ? compositionEdges(model) : relationEdges(model);
  return [...source, ...(options.connections === 'relations' ? wiringEdges(model) : [])];
}

const SITUATIONAL = 'situational';

const onlyRequiredCompositionIsDrawn = (options: ViewOptions): boolean =>
  options.connections === 'composition' && options.display === 'lines' && options.lineStyle === 'uniform';

export function visibleEdges(model: ExplorerModel, options: ViewOptions, layout: Layout, selection: Selection): DisplayEdge[] {
  const present = new Set(layout.cards.map((c) => c.id));
  const source = baseEdges(model, options);
  const asked = (edges: DisplayEdge[]): DisplayEdge[] =>
    onlyRequiredCompositionIsDrawn(options) ? edges.filter((edge) => edge.strength !== SITUATIONAL) : edges;
  if (options.view === 'elements') {
    const drawable = source.filter((edge) => [edge.from, edge.to, ...(edge.targetPair ?? [])].every((id) => present.has(id)));
    return asked(bundleExpandedPairs(drawable, bundleFocusCard(selection.entity, '', '', selection.connection)));
  }
  const artifactIds = layout.cards.filter((c) => c.kind === 'artifact').map((c) => c.id);
  const rolled = artifactEdges(
    source.filter((edge) => !edge.targetPair),
    compositionEntries(model),
    artifactIds,
    options.connections === 'composition' ? 'composition' : 'relations',
  );
  return asked(collapseCardPairs(rolled.filter((e) => present.has(e.from) && present.has(e.to))));
}

export function relatedTo(edges: DisplayEdge[], focus: string): Set<string> {
  const related = new Set<string>(focus ? [focus] : []);
  for (const edge of edges)
    if (edge.from === focus || edge.to === focus || edge.targetPair?.includes(focus)) {
      related.add(edge.from);
      related.add(edge.to);
      for (const id of edge.targetPair ?? []) related.add(id);
      related.add(edge.path);
    }
  return related;
}

const NUB_OWNER = 'nub:';

export const nubOwnerCard = (connection: string): string => (connection.startsWith(NUB_OWNER) ? connection.slice(NUB_OWNER.length) : '');

export const edgeTouches = (edge: { from: string; to: string; targetPair?: string[] }, id: string): boolean =>
  edge.from === id || edge.to === id || edge.targetPair?.includes(id) === true;

export function cardWithKin(edges: { from: string; to: string; targetPair?: string[] }[], id: string): Set<string> {
  const kin = new Set<string>([id]);
  for (const edge of edges)
    if (edgeTouches(edge, id)) for (const endpoint of [edge.from, edge.to, ...(edge.targetPair ?? [])]) kin.add(endpoint);
  return kin;
}

export function nubLayer(layout: Layout, edges: SceneEdge[], zoom: number): PlacedNub[] {
  const counts = new Map<string, number>();
  for (const edge of edges)
    for (const id of new Set([edge.from, edge.to, ...(edge.targetPair ?? [])]))
      counts.set(id, (counts.get(id) ?? 0) + (edge.sources?.length ?? 1));
  const boundaryById = new Map(layout.boundaries.map((b) => [b.id, b]));
  const scopes = new Map<string, Rect>();
  for (const card of layout.cards) {
    const owner = boundaryById.get(card.scopeId);
    if (owner) scopes.set(card.id, owner);
  }
  return placeNubs(counts, cardRects(layout), scopes, boundaryHeads(layout), zoom);
}

export const boundaryRails = (layout: Layout): HorizontalRail[] =>
  layout.boundaries.flatMap((b) => [
    { x: b.x, y: b.y, w: b.w },
    { x: b.x, y: b.y + b.h, w: b.w },
  ]);

export function labelLayer(layout: Layout, edges: SceneEdge[], candidates: LabelCandidate[], zoom: number): PlacedLabel[] {
  if (!candidates.length) return [];
  return placeLabels(
    candidates,
    [...layout.cards.map((c) => ({ x: c.x, y: c.y, w: c.w, h: c.h })), ...boundaryHeads(layout)],
    zoom,
    polylineCrossings(edges.filter((e) => e.drawn).map((e) => e.points)),
    boundaryRails(layout),
  );
}

export function buildScene(
  model: ExplorerModel,
  options: ViewOptions,
  selection: Selection,
  zoom = 1,
  sampler: PathSampler = straightSampler,
): Scene {
  const layout = layoutFor(model, options);
  const rects = cardRects(layout);
  const edges = visibleEdges(model, options, layout, selection);
  const focus = selection.entity;
  const related = relatedTo(edges, focus);
  const router = new Router();
  router.begin();
  const emphasisActive = options.connections === 'relations' && options.emphasis.length > 0;
  const countsOnly = options.display === 'counts';
  const scened: SceneEdge[] = edges.map((edge) => {
    const a = rects.get(edge.from)!;
    const b = edge.targetPair
      ? (() => {
          const p = rects.get(edge.targetPair[0])!;
          const q = rects.get(edge.targetPair[1])!;
          return { x: (p.x + p.w / 2 + q.x + q.w / 2) / 2, y: (p.y + p.h + q.y) / 2, w: 0, h: 0 };
        })()
      : rects.get(edge.to)!;
    const d = edge.targetPair
      ? `M ${a.x + a.w / 2} ${a.y + a.h} L ${b.x} ${b.y}`
      : router.path(a, b, rects, { from: edge.from, to: edge.to, kind: edge.kind, strength: edge.strength, label: edge.label });
    const points = pathPoints(d);
    const on = !!focus && (edge.from === focus || edge.to === focus || edge.targetPair?.includes(focus) === true);
    const grade: SceneEdge['grade'] =
      edge.targetPair || options.lineStyle !== 'distinct' || options.connections !== 'composition'
        ? null
        : edge.strength === 'situational'
          ? 'situational'
          : edge.strength === 'mixed'
            ? 'mixed'
            : 'required';
    const dash: SceneEdge['dash'] = edge.targetPair ? 'frame' : grade === 'situational' || grade === 'mixed' ? grade : 'none';
    return {
      ...edge,
      drawn: !countsOnly || on || selection.connection === edge.path,
      d,
      points,
      on,
      emphasized: emphasisActive && options.emphasis.includes(edge.kind ?? ''),
      dash,
      grade,
      paint: edge.targetPair ? 'frame' : edge.rolled ? 'rolled' : 'element',
      midpoint: points.length ? points[Math.floor(points.length / 2)] : { x: a.x, y: a.y },
    };
  });

  const cardList = layout.cards.map((c) => ({ x: c.x, y: c.y, w: c.w, h: c.h }));
  let labelCandidates: LabelCandidate[] = [];
  let nubs: PlacedNub[] = [];
  if (countsOnly && !focus) {
    nubs = nubLayer(layout, scened, zoom);
  } else {
    const shown = scened.filter((edge) => edge.drawn && (edge.on || selection.connection === edge.path));
    labelCandidates = shown.map((edge) => {
      const { samples, middle } = sampler(edge.d, sampleCount());
      const numeric = options.view !== 'elements' || !!edge.bundled;
      const count = edge.sources?.length ?? 1;
      return {
        edge: edge.path,
        text: numeric ? (count > MAX_DISPLAY_COUNT ? `${MAX_DISPLAY_COUNT}+` : String(count)) : edge.label,
        numeric,
        samples,
        middle,
      };
    });
  }
  const labels = labelLayer(layout, scened, labelCandidates, zoom);
  return { layout, edges: scened, labelCandidates, labels, nubs, related, focus, zoom, bounds: union([...cardList, ...layout.boundaries]) };
}

export const LEGEND_ROWS = ['direct', 'rolled', 'required', 'situational', 'mixed', 'owns', 'links'] as const;

export type LegendRow = (typeof LEGEND_ROWS)[number];

export const LEGEND_ROW_HOLDING: Partial<Record<LegendRow, Holding>> = { owns: 'owns', links: 'links' };

const drawnEdgeEachLegendRowDescribes: Record<LegendRow, (edge: SceneEdge) => boolean> = {
  direct: (edge) => edge.paint === 'element',
  rolled: (edge) => edge.paint === 'rolled',
  required: (edge) => edge.grade === 'required',
  situational: (edge) => edge.grade === 'situational',
  mixed: (edge) => edge.grade === 'mixed',
  owns: (edge) => holdingDrawn(edge) === 'owns',
  links: (edge) => holdingDrawn(edge) === 'links',
};

export const legendRows = (scene: Scene): LegendRow[] =>
  LEGEND_ROWS.filter((row) => scene.edges.some((edge) => edge.drawn && drawnEdgeEachLegendRowDescribes[row](edge)));

export function subjectBounds(scene: Scene, selection: Selection): Rect | null {
  const subject = selection.entity || nubOwnerCard(selection.connection) || selection.option;
  if (subject) {
    const card = scene.layout.cards.find((c) => c.id === subject);
    if (card) return { x: card.x, y: card.y, w: card.w, h: card.h };
    const boundary = scene.layout.boundaries.find((b) => b.id === subject);
    if (boundary) return boundary;
  }
  if (selection.connection) {
    const edge = scene.edges.find((e) => e.path === selection.connection);
    if (edge?.points.length) return union(edge.points.map((p) => ({ x: p.x, y: p.y, w: 0, h: 0 })));
  }
  return null;
}

export function selectionBounds(scene: Scene, selection: Selection): Rect | null {
  const ids = new Set<string>();
  const nubOwner = nubOwnerCard(selection.connection);
  if (nubOwner) for (const id of cardWithKin(scene.edges, nubOwner)) ids.add(id);
  else if (selection.connection) {
    const edge = scene.edges.find((e) => e.path === selection.connection);
    if (edge) {
      ids.add(edge.from);
      ids.add(edge.to);
      for (const id of edge.targetPair ?? []) ids.add(id);
    }
  } else if (selection.entity) for (const id of scene.related) ids.add(id);
  else if (selection.option) ids.add(selection.option);
  const boxes: Rect[] = scene.layout.cards.filter((c) => ids.has(c.id)).map((c) => ({ x: c.x, y: c.y, w: c.w, h: c.h }));
  for (const boundary of scene.layout.boundaries) if (ids.has(boundary.id)) boxes.push(boundary);
  for (const edge of scene.edges)
    if ((selection.connection && edge.path === selection.connection) || (selection.entity && edge.on))
      boxes.push(union(edge.points.map((p) => ({ x: p.x, y: p.y, w: 0, h: 0 }))));
  return boxes.length ? union(boxes) : null;
}
