import test from 'node:test';
import assert from 'node:assert/strict';
import { type CompositionMember, type CompositionGroup, answerOwners, compositionGroups, holdingOf } from '@/src/lib/composition-grouping';
import { endsOfConnectionPanel } from '@/src/lib/connection-reading';
import { type DisplayEdge, type Provenance, compositionEntries, emptySelection, initialOptions, updateOptions } from '@/src/lib/model';
import { buildScene } from '@/src/lib/scene';
import { model } from './render-states';

const entries = compositionEntries(model);
const owners = answerOwners(entries);

const membersByOwner = (): Map<string, CompositionMember[]> => {
  const held = new Map<string, CompositionMember[]>();
  for (const entry of entries) {
    const list = held.get(entry.from);
    const member: CompositionMember = { target: entry.to, from: entry.from, strength: entry.strength, mode: entry.mode, when: entry.when };
    if (list) list.push(member);
    else held.set(entry.from, [member]);
  }
  return held;
};

const panelsOfEveryOwner = (): { owner: string; groups: CompositionGroup[] }[] =>
  [...membersByOwner()].map(([owner, members]) => ({ owner, groups: compositionGroups(members, owners) }));

const membersByAnswer = (): Map<string, CompositionMember[]> => {
  const held = new Map<string, CompositionMember[]>();
  for (const entry of entries) {
    const member: CompositionMember = {
      target: entry.from,
      answer: entry.to,
      strength: entry.strength,
      mode: entry.mode,
      when: entry.when,
    };
    const list = held.get(entry.to);
    if (list) list.push(member);
    else held.set(entry.to, [member]);
  }
  return held;
};

const panels = [
  ...panelsOfEveryOwner(),
  ...[...membersByAnswer()].map(([subject, members]) => ({ owner: subject, groups: compositionGroups(members, owners) })),
];

test('every composition row resolves to one holding, and states no predicate its group already states', () => {
  const declared = new Map(
    entries.flatMap((entry) => [
      [`${entry.from} ${entry.to}`, holdingOf(entry)] as const,
      [`${entry.to} ${entry.from}`, holdingOf(entry)] as const,
    ]),
  );
  const failures: string[] = [];
  for (const { owner, groups } of panels)
    for (const group of groups) {
      if (!group.predicate) failures.push(`${owner} draws a group of ${group.rows.length} rows that states no predicate`);
      for (const row of group.rows) {
        const expected = declared.get(`${owner} ${row.target}`);
        if (row.holding !== expected)
          failures.push(`${owner} · ${row.target} resolves to ${row.holding}, and the universe declares ${expected}`);
        if (row.predicate) failures.push(`${owner} · ${row.target} repeats '${row.predicate}' under a group that already states one`);
      }
    }
  assert.deepEqual(failures.slice(0, 4), []);
});

test('a row whose answer is kept elsewhere names where', () => {
  const known = new Set(model.entities.map((entity) => entity.id));
  const failures: string[] = [];
  let linked = 0;
  for (const { owner, groups } of panels)
    for (const group of groups)
      for (const row of group.rows) {
        if (row.holding === 'owns') {
          if (row.destination) failures.push(`${owner} · ${row.target} keeps its own answer and names ${row.destination} anyway`);
          continue;
        }
        linked += 1;
        if (!row.destination || !known.has(row.destination))
          failures.push(`${owner} · ${row.target} points elsewhere and names ${row.destination ?? 'nowhere'}`);
      }
  assert.ok(linked > 0, 'the universe must declare at least one row that points elsewhere for this to mean anything');
  assert.deepEqual(failures.slice(0, 4), []);
});

const countedBoard = buildScene(model, updateOptions(initialOptions(), { view: 'elements', display: 'counts' }), emptySelection());

const provenancesTouching = (card: string): Provenance[] =>
  countedBoard.edges
    .filter((edge) => edge.from === card || edge.to === card || edge.targetPair?.includes(card))
    .flatMap((edge) => edge.sources ?? [{ source: edge as DisplayEdge, composition: [] }]);

const countBadgeEdge = (card: string): DisplayEdge => ({
  path: `nub:${card}`,
  from: card,
  to: card,
  label: 'Connections',
  ordered: false,
  nub: true,
  sources: provenancesTouching(card),
});

const otherEndsAround = (card: string): Set<string> => {
  const ends = new Set<string>();
  for (const provenance of provenancesTouching(card))
    for (const id of [provenance.source.from, provenance.source.to]) if (id !== card) ends.add(id);
  return ends;
};

test('a panel whose sources share one other end is headed by both ends, and one with several is not', () => {
  const cards = countedBoard.layout.cards.map((card) => card.id);
  const oneNeighbour = cards.find((card) => otherEndsAround(card).size === 1);
  const manyNeighbours = cards.find((card) => otherEndsAround(card).size > 1);
  assert.ok(oneNeighbour, 'the board must carry a card with exactly one neighbour');
  assert.ok(manyNeighbours, 'the board must carry a card with several neighbours');
  const only = [...otherEndsAround(oneNeighbour)][0];
  assert.equal(
    endsOfConnectionPanel(model, countBadgeEdge(oneNeighbour), provenancesTouching(oneNeighbour)).other,
    only,
    `${oneNeighbour} sits opposite ${only} on every source its panel lists`,
  );
  assert.equal(endsOfConnectionPanel(model, countBadgeEdge(manyNeighbours), provenancesTouching(manyNeighbours)).other, null);
});
