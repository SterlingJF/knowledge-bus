import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  type ExplorerModel,
  validateModel,
  initialOptions,
  updateOptions,
  emptySelection,
  referencedFrames,
  relationKinds,
} from '@/src/lib/model';
import { layoutFor, passesFrameFilter } from '@/src/lib/layout';
import { buildScene, selectionBounds, subjectBounds } from '@/src/lib/scene';
import { cardAnatomy } from '@/src/lib/card';
import { serializeSvg } from '@/src/lib/export';
import { emphasise } from '@/src/lib/emphasis';
import {
  constrainCamera,
  fitCamera,
  fitCameraWithin,
  frameCamera,
  noInsets,
  zoomAround,
  interpolate,
  boundaryScale,
  MIN_ZOOM,
  MAX_ZOOM,
} from '@/src/lib/camera';
import { intersects } from '@/src/lib/geometry';

const model = validateModel(JSON.parse(readFileSync(new URL('../fixtures/product-development.json', import.meta.url), 'utf8')));
const viewport = { width: 1280, height: 720 };

test('the guards refuse broken shapes and invalid view options', () => {
  assert.throws(() => validateModel({ ...model, schema: 'knowledge-bus/explorer-model/99' }));
  assert.throws(() => validateModel({ ...model, wiring: [{ ...model.wiring[0], to: 'element:missing' }] }));
  assert.throws(() => validateModel({ ...model, connections: [{ ...model.connections[0], to: 'element:missing' }] }));
  assert.throws(() => updateOptions(initialOptions(), { connections: 'nonsense' } as never));
});

test('grouped elements sit inside their ordering boundary; ungrouped keeps every element', () => {
  const grouped = layoutFor(model, initialOptions());
  const phases = new Map(grouped.boundaries.filter((b) => b.role === 'group').map((boundary) => [boundary.id, boundary]));
  const elements = new Set(model.entities.filter((entity) => entity.kind === 'element').map((entity) => entity.id));
  assert.deepEqual(new Set(grouped.cards.filter((card) => card.kind === 'element').map((card) => card.id)), elements);
  for (const card of grouped.cards.filter((c) => c.kind === 'element')) {
    const owner = phases.get(card.scopeId);
    assert.ok(owner, `${card.id} has no phase boundary`);
    assert.ok(
      card.x >= owner.x && card.y >= owner.y && card.x + card.w <= owner.x + owner.w && card.y + card.h <= owner.y + owner.h,
      `${card.id} lies outside its phase boundary`,
    );
  }
  const flat = layoutFor(model, updateOptions(initialOptions(), { group: false }));
  assert.deepEqual(new Set(flat.cards.filter((card) => card.kind === 'element').map((card) => card.id)), elements);
  assert.equal(flat.boundaries.filter((b) => b.role === 'group').length, 0);
});

test('frame filters combine with OR inside a frame and AND across frames', () => {
  const sample: ExplorerModel = {
    schema: 'knowledge-bus/explorer-model/1',
    protocolVersion: 'test',
    sourceDigest: '',
    universe: { id: 'filters', label: 'Filters', version: 1, ordering_frame: '' },
    orderingFrameId: '',
    entities: [
      ['alpha', 'start', 'team'],
      ['beta', 'end', 'team'],
      ['gamma', 'start', 'individual'],
    ].map(([sourceId, stage, audience]) => ({
      id: `element:${sourceId}`,
      sourceId,
      kind: 'element',
      label: sourceId,
      description: '',
      frameValues: { stage, audience },
      raw: {},
    })),
    connections: [],
    wiring: [],
    rules: [],
    source: {},
    evaluation: { status: 'unevaluated', context: null },
  };
  const start = 'option:stage:start';
  const end = 'option:stage:end';
  assert.ok(passesFrameFilter(sample, 'element:alpha', [start]));
  assert.ok(!passesFrameFilter(sample, 'element:alpha', [end]));
  assert.ok(passesFrameFilter(sample, 'element:alpha', [end, start]));
  assert.ok(!passesFrameFilter(sample, 'element:alpha', [start, 'option:audience:individual']));
  assert.ok(!passesFrameFilter(sample, 'element:alpha', [start, 'frame:missing']));
  assert.ok(passesFrameFilter(sample, 'element:alpha', []));
  const filtered = layoutFor(sample, updateOptions(initialOptions(), { group: false, frames: [start, 'option:audience:team'] }));
  assert.deepEqual(
    filtered.cards.map((card) => card.id),
    ['element:alpha'],
  );
});

test('canonical product-development cards carry their declared ordering icon, cardinality, and frame references', () => {
  const layout = layoutFor(model, initialOptions());
  const vision = layout.cards.find((c) => c.id === 'element:product-vision')!;
  const anatomy = cardAnatomy(vision, model);
  assert.deepEqual(anatomy.icon, model.marks!.declared['option:phase:strategy']);
  assert.equal(anatomy.subtitle, 'One answer');
  assert.equal(anatomy.edge, 'left');
  const gated = layout.cards.find((c) => c.id === 'element:positioning-statement')!;
  assert.deepEqual(cardAnatomy(gated, model).frameNames, ['Uptake']);
  assert.deepEqual(referencedFrames(model, 'artifact:design-doc').sort(), ['authority', 'reversibility']);
});

test('composition is the opening connection, counts place badges, and labels wait for a selection', () => {
  const counts = buildScene(model, updateOptions(initialOptions(), { display: 'counts' }), emptySelection());
  const connected = new Set(
    model.connections.filter((connection) => connection.kind === 'composition').flatMap((connection) => [connection.from, connection.to]),
  );
  assert.deepEqual(new Set(counts.nubs.map((nub) => nub.id)), connected);
  assert.equal(counts.labels.length, 0);
  assert.ok(counts.edges.every((e) => e.kind === 'composition'));
  const lineOptions = updateOptions(initialOptions(), { connections: 'relations', display: 'lines' });
  const idle = buildScene(model, lineOptions, emptySelection());
  assert.equal(idle.labels.length, 0);
  assert.equal(idle.nubs.length, 0);
  const selected = buildScene(model, lineOptions, { entity: 'element:value-proposition', connection: '', option: '' });
  assert.ok(selected.labels.length > 0);
  assert.ok(selected.labels.some((l) => !l.numeric));
  const kinds = new Set(relationKinds(model).map((k) => k.id));
  for (const label of selected.labels) assert.ok(!kinds.has(label.text), `label shows the raw kind ${label.text}`);
  const off = buildScene(model, updateOptions(initialOptions(), { connections: '' }), emptySelection());
  assert.equal(off.edges.length, 0);
});

test('line style marks situational memberships only when asked', () => {
  const uniform = buildScene(model, updateOptions(initialOptions(), { lineStyle: 'uniform' }), emptySelection());
  assert.ok(uniform.edges.every((e) => e.dash === 'none'));
  const distinct = buildScene(model, updateOptions(initialOptions(), { lineStyle: 'distinct', display: 'lines' }), emptySelection());
  assert.ok(distinct.edges.some((e) => e.dash === 'situational'));
});

test('one composition setting draws only the connections that are not situational; the other draws them all', () => {
  for (const view of ['elements', 'artifacts'] as const) {
    const lines = updateOptions(initialOptions(), { view, connections: 'composition', display: 'lines' });
    const all = buildScene(model, updateOptions(lines, { lineStyle: 'distinct' }), emptySelection());
    const required = buildScene(model, updateOptions(lines, { lineStyle: 'uniform' }), emptySelection());
    const situational = (edges: { strength?: string }[]) => edges.filter((edge) => edge.strength === 'situational');
    const paths = (edges: { path: string }[]) => edges.map((edge) => edge.path).sort();
    assert.ok(situational(all.edges).length > 0, `${view} draws no situational connection, so this asserts nothing`);
    assert.deepEqual(
      situational(required.edges).map((edge) => (edge as { path: string }).path),
      [],
      view,
    );
    assert.deepEqual(paths(required.edges), paths(all.edges.filter((edge) => edge.strength !== 'situational')), view);
  }
});

test('the panel places itself against the subject itself, which is smaller than the set the camera frames', () => {
  const selection = { ...emptySelection(), entity: 'artifact:product-strategy-canvas' };
  const scene = buildScene(model, initialOptions(), selection);
  const card = scene.layout.cards.find((c) => c.id === selection.entity)!;
  assert.deepEqual(subjectBounds(scene, selection), { x: card.x, y: card.y, w: card.w, h: card.h });
  const framed = selectionBounds(scene, selection)!;
  assert.ok(framed.h > card.h, 'the framed set is no larger than the subject, so the two cannot be told apart');
  assert.equal(subjectBounds(scene, emptySelection()), null);
});

test('the artifact view rolls element relations up and marks them rolled', () => {
  const scene = buildScene(
    model,
    updateOptions(initialOptions(), { view: 'artifacts', connections: 'relations', display: 'lines' }),
    emptySelection(),
  );
  assert.ok(scene.edges.length);
  assert.ok(scene.edges.some((e) => e.rolled));
  assert.ok(scene.edges.every((e) => scene.layout.cards.some((c) => c.id === e.from) && scene.layout.cards.some((c) => c.id === e.to)));
});

test('selecting a card relates its neighbours and frames them inside the safe area', () => {
  const selection = { ...emptySelection(), entity: 'artifact:product-strategy-canvas' };
  const scene = buildScene(model, initialOptions(), selection);
  assert.ok(scene.related.size > 1);
  assert.ok(scene.related.has('element:product-vision'));
  const bounds = selectionBounds(scene, selection)!;
  const insets = { left: 372, right: 0, top: 0, bottom: 68 };
  const camera = frameCamera(bounds, viewport, insets)!;
  const left = bounds.x * camera.z + camera.x;
  const right = (bounds.x + bounds.w) * camera.z + camera.x;
  assert.ok(left >= insets.left, 'selection is not hidden behind the overlay');
  assert.ok(right <= viewport.width);
  assert.ok(camera.z <= 1.2);
});

test('a count badge selection frames the card its emphasis activates, together with that card kin', () => {
  const options = updateOptions(initialOptions(), { display: 'counts' });
  const idle = buildScene(model, options, emptySelection());
  assert.ok(idle.nubs.length > 0, 'the counts display places count badges');
  const badge = idle.nubs.find((nub) => idle.layout.cards.some((c) => c.id === nub.id))!;
  const selection = { entity: '', connection: `nub:${badge.id}`, option: '' };
  const scene = buildScene(model, options, selection);
  const shown = emphasise(scene, selection, '');
  const subject = scene.layout.cards.filter((card) => shown.cards.get(card.id) !== 'dimmed');
  assert.ok(
    subject.some((card) => card.id === badge.id),
    'the badge owner is part of its own emphasis subject',
  );
  assert.ok(subject.length > 1, 'the badge owner has kin to frame');
  const bounds = selectionBounds(scene, selection);
  assert.ok(bounds, 'a count badge selection gives the camera bounds to frame');
  for (const card of subject)
    assert.ok(
      card.x >= bounds!.x && card.y >= bounds!.y && card.x + card.w <= bounds!.x + bounds!.w && card.y + card.h <= bounds!.y + bounds!.h,
      `${card.id} is emphasised but falls outside the framed bounds`,
    );
  assert.ok(bounds!.w < scene.bounds.w || bounds!.h < scene.bounds.h, 'framing a count badge is tighter than framing the whole map');
});

test('the camera stays finite, clamps zoom, and keeps content reachable', () => {
  const scene = buildScene(model, initialOptions(), emptySelection());
  const fit = fitCamera(scene.bounds, viewport);
  assert.ok(Number.isFinite(fit.x) && Number.isFinite(fit.y) && fit.z > 0);
  const runaway = constrainCamera({ x: 1e8, y: -1e8, z: 1 }, scene.bounds, viewport);
  assert.ok(Math.abs(runaway.x) < 1e6 && Math.abs(runaway.y) < 1e6);
  assert.equal(zoomAround({ x: 0, y: 0, z: 1 }, 99, 0, 0).z, MAX_ZOOM);
  assert.equal(zoomAround({ x: 0, y: 0, z: 1 }, 0.001, 0, 0).z, MIN_ZOOM);
  const pivot = { x: 300, y: 200 };
  const before = { x: 100, y: 50, z: 1 };
  const after = zoomAround(before, 1.5, pivot.x, pivot.y);
  assert.ok(Math.abs((pivot.x - before.x) / before.z - (pivot.x - after.x) / after.z) < 1e-9);
  assert.deepEqual(interpolate(before, after, 0), before);
  assert.deepEqual(interpolate(before, after, 1), after);
  assert.deepEqual(interpolate(before, after, 5), after);
  assert.equal(boundaryScale(0.1), 1.25);
  assert.equal(boundaryScale(2), 1);
});

test('fitting the map while the detail panel is open keeps the map clear of the panel', () => {
  const scene = buildScene(model, initialOptions(), emptySelection());
  assert.deepEqual(
    fitCameraWithin(scene.bounds, viewport, noInsets()),
    fitCamera(scene.bounds, viewport),
    'with no insets the fit is the one the map has always used',
  );
  const insets = { left: 372, right: 0, top: 64, bottom: 68 };
  const camera = fitCameraWithin(scene.bounds, viewport, insets);
  const left = scene.bounds.x * camera.z + camera.x;
  const right = (scene.bounds.x + scene.bounds.w) * camera.z + camera.x;
  const top = scene.bounds.y * camera.z + camera.y;
  assert.ok(left >= insets.left, 'the fitted map is not hidden behind the overlay');
  assert.ok(right <= viewport.width - insets.right);
  assert.ok(top >= insets.top);
  assert.ok(camera.z < fitCamera(scene.bounds, viewport).z, 'fitting into the smaller safe area zooms out, it does not crop');
});

test('the export carries every visible card, both themes, and no scripts or external references', () => {
  const scene = buildScene(model, initialOptions(), emptySelection());
  const svg = serializeSvg(scene, model, 'auto');
  assert.equal(svg, serializeSvg(buildScene(model, initialOptions(), emptySelection()), model, 'auto'));
  assert.equal((svg.match(/<g data-entity=/g) ?? []).length, scene.layout.cards.length);
  for (const boundary of scene.layout.boundaries) if (boundary.title) assert.ok(svg.includes(`>${boundary.title}<`), boundary.title);
  assert.match(svg, /prefers-color-scheme:light/);
  assert.doesNotMatch(svg, /<script|foreignObject|\son[a-z]+=|<image|xlink:href/);
  assert.doesNotMatch(svg, /https?:\/\/(?!www\.w3\.org)/);
  assert.doesNotMatch(svg, /light-dark\(/);
  assert.doesNotMatch(svg, /\/Users\//);
  assert.match(svg, /width="100%" height="100%"/);
  assert.match(svg, /preserveAspectRatio="xMidYMid meet"/);
  const declared = new Set([...svg.matchAll(/(--[\w-]+):/g)].map((m) => m[1]));
  for (const [, name] of svg.matchAll(/var\((--[\w-]+)/g)) assert.ok(declared.has(name), `unresolved ${name}`);
});

test('universe text reaches the export as inert data', () => {
  const hostile = structuredClone(model);
  hostile.universe.label = '</style><script>alert(1)</script>';
  hostile.entities.find((e) => e.kind === 'artifact')!.label = '<img src=x onerror=alert(1)>';
  const svg = serializeSvg(buildScene(hostile, initialOptions(), emptySelection()), hostile, 'auto');
  assert.doesNotMatch(svg, /<script|\son[a-z]+\s*=\s*["']/);
  assert.equal((svg.match(/<style>/g) ?? []).length, 1);
  assert.equal((svg.match(/<\/style>/g) ?? []).length, 1);
  assert.match(svg, /&lt;img/);
  assert.match(svg, /onerror=alert\(1\)&gt;/);
  assert.match(svg, /&lt;\/style&gt;&lt;script&gt;/);
});
