import test from 'node:test';
import assert from 'node:assert/strict';
import { type Boundary, type Layout, layoutFor } from '@/src/lib/layout';
import { type Entity, type ExplorerModel, initialOptions, updateOptions } from '@/src/lib/model';
import { roleCopy } from '@/src/lib/phrasing';
import { model } from './render-states';

const framesView = (subject: ExplorerModel): Layout => layoutFor(subject, updateOptions(initialOptions(), { view: 'frames' }));

const aFactorTheUniverseDoesNotHave = (): Entity => ({
  id: 'factor:sample',
  sourceId: 'sample',
  kind: 'factor',
  label: 'Sample condition',
  description: '',
  frameValues: {},
  raw: {},
});

const withOneFactor = (subject: ExplorerModel): ExplorerModel => ({
  ...subject,
  entities: [...subject.entities, aFactorTheUniverseDoesNotHave()],
});

const boundariesStatingARule = (layout: Layout): Set<string> =>
  new Set(layout.cards.filter((card) => card.kind === 'rule').map((card) => card.scopeId));

const dimensionBoundaries = (layout: Layout): Boundary[] => layout.boundaries.filter((boundary) => !boundary.scopeId);

const FRAMES_CAPTION = 'Your situation. These change what you need.';
const EXCEPTIONS_CAPTION = 'Your special cases. These mean no artifact is needed.';
const FACTORS_CAPTION = 'Your conditions. These shape how you go about the work.';
const FACTORS_NONE = 'This universe declares no factors.';

const whatEachBoundaryHolds = (layout: Layout): Set<string> => {
  const held = new Set<string>();
  for (const card of layout.cards) held.add(card.scopeId);
  for (const note of layout.notes) held.add(note.scopeId);
  for (const boundary of layout.boundaries) if (boundary.scopeId) held.add(boundary.scopeId);
  return held;
};

test('the frames view draws two top-level boundaries, Frames and Factors, and every frame the universe declares is drawn inside Frames', () => {
  const populated = withOneFactor(model);
  const layout = framesView(populated);
  const dimensions = dimensionBoundaries(layout);
  assert.deepEqual(
    dimensions.map((boundary) => boundary.title),
    ['Frames', 'Factors'],
  );
  const frames = dimensions[0];
  const ordering = layout.boundaries.find((boundary) => boundary.id === populated.orderingFrameId);
  assert.ok(ordering, 'the ordering frame is drawn as a boundary of its own');
  assert.equal(ordering.scopeId, frames.id, 'the ordering frame is nested inside Frames');

  const heldBy = new Map<string, string>();
  for (const card of layout.cards) heldBy.set(card.id, card.scopeId);
  for (const boundary of layout.boundaries) heldBy.set(boundary.id, boundary.scopeId);
  const framesDeclared = populated.entities.filter((entity) => entity.kind === 'frame');
  const misplaced = framesDeclared
    .map((entity) => [entity.id, heldBy.get(entity.id)] as const)
    .filter(([, owner]) => owner !== frames.id)
    .map(([id, owner]) => `${id} is held by ${owner ?? 'nothing drawn'} rather than ${frames.id}`);
  assert.deepEqual(misplaced, []);

  const rules = [...boundariesStatingARule(layout)];
  assert.deepEqual(rules, ['scope:rule'], 'declared rules share the Exceptions boundary');
  const exceptions = layout.boundaries.find((boundary) => boundary.id === rules[0]);
  assert.ok(exceptions, 'the rule boundary is drawn');
  assert.equal(exceptions.scopeId, frames.id, 'the rule boundary is nested inside Frames');
  assert.deepEqual(
    new Set(layout.cards.filter((card) => card.scopeId === exceptions.id).map((card) => card.id)),
    new Set(populated.rules.map((rule) => rule.id)),
    'Exceptions holds every declared rule and nothing else',
  );
});

test('no dimension boundary is titled with a frame role or a phrase describing one', () => {
  const layout = framesView(withOneFactor(model));
  const roles = [...new Set(model.entities.filter((e) => e.kind === 'frame').map((e) => String(e.raw.role)))].filter(Boolean);
  const STOPWORDS = new Set([
    'the',
    'a',
    'an',
    'is',
    'are',
    'which',
    'what',
    'how',
    'when',
    'no',
    'not',
    'in',
    'of',
    'to',
    'and',
    'or',
    'its',
    'this',
    'that',
    'these',
    'it',
    'for',
    'on',
    'by',
    'with',
    'be',
    'whether',
    'one',
    'own',
    'your',
  ]);
  const STEM = 5;
  const stems = (phrase: string): string[] =>
    phrase
      .toLowerCase()
      .split(/[^a-z]+/)
      .filter((word) => word && !STOPWORDS.has(word))
      .map((word) => word.slice(0, STEM));
  const describingARole = new Map<string, string>();
  for (const role of roles) for (const stem of stems(roleCopy(role))) describingARole.set(stem, role);
  const failures: string[] = [];
  for (const boundary of dimensionBoundaries(layout)) {
    const title = boundary.title.toLowerCase();
    for (const role of roles)
      if (title.includes(role)) failures.push(`${boundary.id} is titled '${boundary.title}', naming the role ${role}`);
    for (const stem of stems(boundary.title)) {
      const role = describingARole.get(stem);
      if (role) failures.push(`${boundary.id} is titled '${boundary.title}', which describes the ${role} role rather than naming a thing`);
    }
  }
  assert.deepEqual(failures, []);
});

test('Frames, Exceptions and Factors are the only boundaries that carry a caption, and their captions are the authored ones', () => {
  const layout = framesView(withOneFactor(model));
  assert.deepEqual(
    layout.boundaries.filter((boundary) => boundary.caption).map((boundary) => [boundary.title, boundary.caption]),
    [
      ['Frames', FRAMES_CAPTION],
      ['Exceptions', EXCEPTIONS_CAPTION],
      ['Factors', FACTORS_CAPTION],
    ],
  );
});

test('a universe declaring no factor still draws Factors, holding the copy that says so', () => {
  const layout = framesView({ ...model, entities: model.entities.filter((entity) => entity.kind !== 'factor') });
  const factors = dimensionBoundaries(layout).find((boundary) => boundary.title === 'Factors');
  assert.ok(factors, 'Factors is the only place a reader learns factors exist, so it is drawn even when none are declared');
  assert.deepEqual(
    layout.cards.filter((card) => card.scopeId === factors.id).map((card) => card.id),
    [],
    'the universe under test must declare no factor for this case to mean anything',
  );
  assert.deepEqual(
    layout.notes.filter((note) => note.scopeId === factors.id).map((note) => note.text),
    [FACTORS_NONE],
  );
  assert.equal(factors.caption, FACTORS_CAPTION);
});

test('a universe declaring no factor draws no boundary around none, and Factors alone is drawn around what it says instead', () => {
  const layout = framesView(model);
  assert.deepEqual(
    dimensionBoundaries(layout).map((boundary) => boundary.title),
    ['Frames', 'Factors'],
  );
  const held = whatEachBoundaryHolds(layout);
  assert.deepEqual(
    layout.boundaries.filter((boundary) => !held.has(boundary.id)).map((boundary) => boundary.id),
    [],
    'every boundary drawn holds a card, a nested boundary, or the note that stands in for the cards it has none of',
  );
  const noteless = framesView({ ...model, rules: [] });
  const itsFactors = dimensionBoundaries(noteless).find((boundary) => boundary.title === 'Factors')!;
  assert.deepEqual(
    noteless.notes.map((note) => note.scopeId),
    [itsFactors.id],
    'no boundary but Factors earns a note when it holds nothing',
  );
  assert.equal(
    noteless.boundaries.find((boundary) => boundary.title === 'Exceptions'),
    undefined,
    'the general rule still holds: a universe stating no rule draws no Exceptions boundary',
  );
});
