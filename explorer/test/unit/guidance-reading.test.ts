import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { type ExplorerModel, validateModel } from '@/src/lib/model';
import {
  guidanceEntries,
  guidanceFor,
  guidanceKindIds,
  subjectsCarryingGuidance,
  subjectsTheGuidanceLeavesBare,
} from '@/src/lib/guidance-reading';

const model = validateModel(JSON.parse(readFileSync(new URL('../fixtures/product-development.json', import.meta.url), 'utf8')));

const ATTACHES_TO = ['element', 'artifact', 'factor'];

test('every claim the document makes is reachable from exactly one subject, in the order the document wrote it', () => {
  const entries = guidanceEntries(model);
  assert.ok(entries.length > 0, 'the fixture must carry guidance for this to be able to fail');
  const ids = new Set(model.entities.map((e) => e.id));
  const reached = subjectsCarryingGuidance(model).flatMap((subject) => {
    assert.ok(ids.has(subject), `${subject} carries guidance but is no entity in the model`);
    return guidanceFor(model, subject);
  });
  assert.equal(reached.length, entries.length);
  assert.deepEqual(new Set(reached.map((e) => e.id)).size, entries.length, 'a claim reachable twice would be drawn twice');
  for (const subject of subjectsCarryingGuidance(model))
    assert.deepEqual(
      guidanceFor(model, subject).map((e) => e.sourcePath),
      entries.filter((e) => e.subject === subject).map((e) => e.sourcePath),
    );
});

test('a subject the document leaves bare reads as bare, not as missing', () => {
  const bare = subjectsTheGuidanceLeavesBare(model, ATTACHES_TO);
  assert.ok(bare.length > 0, 'the universe must hold an unguided subject for the empty case to be under test');
  const carried = new Set(subjectsCarryingGuidance(model));
  for (const subject of bare) {
    assert.ok(!carried.has(subject));
    assert.deepEqual(guidanceFor(model, subject), []);
  }
});

test('a model carrying no guidance document reads as empty rather than throwing', () => {
  const bare = validateModel({ ...(structuredClone(model) as ExplorerModel), guidance: null });
  assert.deepEqual(guidanceEntries(bare), []);
  assert.deepEqual(guidanceKindIds(bare), []);
  assert.deepEqual(guidanceFor(bare, model.entities[0].id), []);
  assert.equal(subjectsTheGuidanceLeavesBare(bare, ATTACHES_TO).length, model.entities.filter((e) => ATTACHES_TO.includes(e.kind)).length);
});

test('guidance naming a subject or a kind the model does not declare refuses rather than rendering it', () => {
  const declared = guidanceKindIds(model);
  assert.ok(declared.length > 0);
  for (const patch of [{ subject: 'element:not-in-this-universe' }, { kind: `${declared[0]}-that-was-never-declared` }]) {
    const broken = structuredClone(model) as ExplorerModel;
    Object.assign(broken.guidance!.entries[0], patch);
    assert.throws(() => validateModel(broken), /guidance/i);
  }
});
