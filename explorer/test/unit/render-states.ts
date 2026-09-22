import { readFileSync } from 'node:fs';
import {
  type ExplorerModel,
  type Selection,
  type ViewOptions,
  emptySelection,
  initialOptions,
  updateOptions,
  validateModel,
} from '@/src/lib/model';
import { buildScene, edgeTouches, labelLayer, nubLayer, type Scene } from '@/src/lib/scene';

export const model: ExplorerModel = validateModel(
  JSON.parse(readFileSync(new URL('../fixtures/product-development.json', import.meta.url), 'utf8')),
);

export interface RenderState {
  name: string;
  options: ViewOptions;
  selection: Selection;
  zoom?: number;
}

const once = <T>(compute: () => T): (() => T) => {
  let cached: T | null = null;
  return () => (cached ??= compute());
};

function optionStates(): { name: string; options: ViewOptions }[] {
  const states: { name: string; options: ViewOptions }[] = [];
  const add = (name: string, patch: Partial<ViewOptions>) => states.push({ name, options: updateOptions(initialOptions(), patch) });
  add('frames', { view: 'frames' });
  for (const view of ['artifacts', 'elements'] as const)
    for (const group of view === 'elements' ? [true, false] : [true]) {
      const tag = view === 'elements' ? `${view}/${group ? 'grouped' : 'flat'}` : view;
      add(`${tag}/off`, { view, group, connections: '' });
      add(`${tag}/relations/lines`, { view, group, connections: 'relations', display: 'lines' });
      add(`${tag}/relations/counts`, { view, group, connections: 'relations', display: 'counts' });
      add(`${tag}/composition/lines/uniform`, { view, group, connections: 'composition', display: 'lines', lineStyle: 'uniform' });
      add(`${tag}/composition/lines/distinct`, { view, group, connections: 'composition', display: 'lines', lineStyle: 'distinct' });
      add(`${tag}/composition/counts`, { view, group, connections: 'composition', display: 'counts' });
    }
  return states;
}

const firstSelectableCard = (scene: Scene): string =>
  scene.layout.cards.find((c) => c.kind === 'artifact' || c.kind === 'element')?.id ?? '';

const enumerated: RenderState[] = [];

export function renderStates(): RenderState[] {
  if (!enumerated.length)
    for (const { name, options } of optionStates()) {
      const unselected: RenderState = { name: `${name} · no selection`, options, selection: emptySelection() };
      enumerated.push(unselected);
      const scene = sceneFor(unselected);
      const card = firstSelectableCard(scene);
      if (card) enumerated.push({ name: `${name} · card`, options, selection: { entity: card, connection: '', option: '' } });
      const connection = scene.edges[0]?.path ?? '';
      if (connection) enumerated.push({ name: `${name} · connection`, options, selection: { entity: '', connection, option: '' } });
    }
  return [...enumerated];
}

export const emptyState = (): RenderState => ({
  name: 'elements · filtered to nothing',
  options: updateOptions(initialOptions(), { frames: ['option:phase:nonexistent'] }),
  selection: emptySelection(),
});

export const buildFresh = (state: RenderState): Scene => buildScene(model, state.options, state.selection, state.zoom ?? 1);

const built = new Map<string, Scene>();

const zoomInvariant = new Map<string, Scene>();

const zoomInvariantKey = (state: RenderState): string => JSON.stringify([state.options, state.selection]);

function prototypeFor(state: RenderState): Scene {
  const key = zoomInvariantKey(state);
  const cached = zoomInvariant.get(key);
  if (cached) return cached;
  const scene = buildScene(model, state.options, state.selection);
  zoomInvariant.set(key, scene);
  return scene;
}

const replayedAtZoom = (prototype: Scene, options: ViewOptions, zoom: number): Scene => ({
  ...prototype,
  zoom,
  labels: labelLayer(prototype.layout, prototype.edges, prototype.labelCandidates, zoom),
  nubs: options.display === 'counts' && !prototype.focus ? nubLayer(prototype.layout, prototype.edges, zoom) : prototype.nubs,
});

export function sceneFor(state: RenderState): Scene {
  const cached = built.get(state.name);
  if (cached) return cached;
  const prototype = prototypeFor(state);
  const zoom = state.zoom ?? 1;
  const scene = zoom === prototype.zoom ? prototype : replayedAtZoom(prototype, state.options, zoom);
  built.set(state.name, scene);
  return scene;
}

export const everyState = (): RenderState[] => [...renderStates(), emptyState()];

const firstOfEachShape = (states: RenderState[], shape: (scene: Scene) => unknown): RenderState[] => {
  const seen = new Set<string>();
  const distinct: RenderState[] = [];
  for (const state of states) {
    const key = JSON.stringify(shape(sceneFor(state)));
    if (seen.has(key)) continue;
    seen.add(key);
    distinct.push(state);
  }
  return distinct;
};

const cardsBoundariesAndNubs = (scene: Scene) => [
  scene.layout.cards.map((c) => [c.id, c.scopeId, c.x, c.y, c.w, c.h]),
  scene.layout.boundaries.map((b) => [b.id, b.x, b.y, b.w, b.h]),
  scene.nubs.map((n) => [n.id, n.inset, n.from.x, n.from.y, n.box.x, n.box.y, n.box.w, n.box.h]),
];

export const geometryStates = once((): RenderState[] => firstOfEachShape(everyState(), cardsBoundariesAndNubs));

export const routeStates = once((): RenderState[] => everyState().filter((state) => sceneFor(state).edges.some((e) => e.drawn)));

export const LABEL_ZOOMS = [1, 0.4096];

const lineStyleIrrelevantOptionsKey = (options: ViewOptions) =>
  JSON.stringify({ view: options.view, group: options.group, connections: options.connections, display: options.display });

function distinctLabelBases(): { name: string; options: ViewOptions; selection: Selection }[] {
  const seen = new Set<string>();
  const bases: { name: string; options: ViewOptions; selection: Selection }[] = [];
  for (const { name, options } of optionStates()) {
    const key = lineStyleIrrelevantOptionsKey(options);
    if (seen.has(key)) continue;
    seen.add(key);
    bases.push({ name: `${name} · no selection`, options, selection: emptySelection() });
  }
  bases.push(emptyState());
  return bases;
}

const aVisibleEdgeTouchesTheCard = (scene: Scene, card: string): boolean => scene.edges.some((edge) => edgeTouches(edge, card));

const aSelectedConnectionIsLabelledRatherThanCounted = (options: ViewOptions): boolean => options.display !== 'counts';

export const labelStates = once((): RenderState[] => {
  const states: RenderState[] = [];
  for (const base of distinctLabelBases()) {
    const scene = sceneFor(base);
    const tag = base.name.replace(' · no selection', '');
    for (const card of scene.layout.cards.filter((c) => c.kind === 'artifact' || c.kind === 'element'))
      if (aVisibleEdgeTouchesTheCard(scene, card.id))
        for (const zoom of LABEL_ZOOMS)
          states.push({
            name: `${tag} · card:${card.id} · z${zoom}`,
            options: base.options,
            selection: { entity: card.id, connection: '', option: '' },
            zoom,
          });
    const connection = scene.edges[0]?.path;
    if (connection && aSelectedConnectionIsLabelledRatherThanCounted(base.options))
      for (const zoom of LABEL_ZOOMS)
        states.push({
          name: `${tag} · connection:${connection} · z${zoom}`,
          options: base.options,
          selection: { entity: '', connection, option: '' },
          zoom,
        });
  }
  return states;
});
