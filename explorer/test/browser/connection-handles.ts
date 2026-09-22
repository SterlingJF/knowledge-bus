import { universeMap } from '@/src/component-patterns/universe-map';
import { showAfterTheLastOfferRests } from '@/src/lib/dwell';
import { labelBox } from '@/src/lib/labels';
import { type ExplorerModel, type Entity } from '@/src/lib/model';
import { type Scene, type SceneEdge } from '@/src/lib/scene';
import { tokenNumber } from '@/src/lib/tokens';
import patternsCss from '@/styles/patterns.css';
import tokensCss from '@/styles/tokens.css';

const entity = (sourceId: string): Entity => ({
  id: `element:${sourceId}`,
  sourceId,
  kind: 'element',
  label: sourceId,
  description: '',
  frameValues: {},
  raw: {},
});
const entities = ['subject', 'offset-target', 'inline-target'].map(entity);
const selection = { entity: entities[0].id, connection: '', option: '' };
const model: ExplorerModel = {
  schema: 'knowledge-bus/explorer-model/1',
  protocolVersion: 'test',
  sourceDigest: '',
  universe: { id: 'handles', label: 'Connection handles', version: 1, ordering_frame: '' },
  orderingFrameId: '',
  entities,
  connections: [],
  wiring: [],
  rules: [],
  source: {},
  evaluation: { status: 'unevaluated', context: null },
};
const edge = (name: string, points: { x: number; y: number }[]): SceneEdge => ({
  path: name,
  from: selection.entity,
  to: `element:${name}-target`,
  label: name,
  ordered: true,
  kind: 'test-relation',
  drawn: true,
  on: true,
  emphasized: false,
  dash: 'none',
  grade: null,
  paint: 'element',
  points,
  d: points.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' '),
  midpoint: points[1],
});
const bounds = { x: 0, y: 0, w: 1000, h: 600 };
const scene: Scene = {
  layout: {
    cards: entities.map((entity, i) => ({
      id: entity.id,
      entity,
      kind: entity.kind,
      scopeId: '',
      x: i ? 750 : 50,
      y: i === 1 ? 100 : i === 2 ? 400 : 250,
      w: 180,
      h: 90,
    })),
    boundaries: [],
    notes: [],
    bounds,
  },
  edges: [
    edge('offset', [
      { x: 230, y: 275 },
      { x: 400, y: 275 },
      { x: 400, y: 145 },
      { x: 750, y: 145 },
    ]),
    edge('inline', [
      { x: 230, y: 310 },
      { x: 550, y: 310 },
      { x: 550, y: 445 },
      { x: 750, y: 445 },
    ]),
  ],
  labels: [
    {
      edge: 'offset',
      text: 'Offset label',
      numeric: false,
      anchor: { x: 580, y: 145 },
      box: labelBox('Offset label', { x: 580, y: 205 }, 1),
    },
    {
      edge: 'inline',
      text: 'Inline label',
      numeric: false,
      anchor: { x: 400, y: 310 },
      box: labelBox('Inline label', { x: 400, y: 310 }, 1),
    },
  ],
  labelCandidates: [],
  nubs: [],
  related: new Set(entities.map((e) => e.id)),
  focus: selection.entity,
  bounds,
  zoom: 1,
};

const host = document.getElementById('explorer')!;
const shadow = host.attachShadow({ mode: 'open' });
const style = document.createElement('style');
style.textContent = tokensCss + patternsCss;
const shell = document.createElement('div');
shell.className = 'shell';
const viewport = document.createElement('div');
viewport.className = 'viewport';
shell.append(viewport);
shadow.append(style, shell);
const dwell = showAfterTheLastOfferRests('', tokenNumber('--kb-motion-dwell'), (id) => map.highlight(selection, id));
const map = universeMap(scene, model, {
  hover: (id) => dwell.offer(id),
  selectEntity: (id) => {
    host.dataset.selectedEntity = id;
  },
  selectConnection: (id) => {
    host.dataset.selectedConnection = id;
  },
});
viewport.append(map.root);
map.applyCamera({ x: 0, y: 0, z: 1 });
map.highlight(selection, '');
