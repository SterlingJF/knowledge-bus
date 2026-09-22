import test from 'node:test';
import assert from 'node:assert/strict';
import { showAfterTheLastOfferRests, type DwellClock } from '@/src/lib/dwell';

function handClock() {
  let now = 0;
  let next = 0;
  const waiting = new Map<number, { due: number; run: () => void }>();
  const started: number[] = [];
  const clock: DwellClock = {
    setTimeout(run, delay) {
      next += 1;
      waiting.set(next, { due: now + delay, run });
      started.push(next);
      return next;
    },
    clearTimeout: (pending) => void waiting.delete(pending as number),
  };
  const pass = (elapsed: number) => {
    now += elapsed;
    for (const [id, timer] of [...waiting]) if (timer.due <= now && waiting.delete(id)) timer.run();
  };
  return { clock, pass, waiting, started };
}

const REST = 90;

test('an offer is shown only once the pointer has rested on it', () => {
  const { clock, pass } = handClock();
  const shown: string[] = [];
  const dwell = showAfterTheLastOfferRests('', REST, (id) => shown.push(id), clock);
  dwell.offer('a');
  pass(REST - 1);
  assert.deepEqual(shown, []);
  assert.equal(dwell.shown(), '');
  pass(1);
  assert.deepEqual(shown, ['a']);
  assert.equal(dwell.shown(), 'a');
});

test('a pointer crossing several subjects shows only the one it rests on', () => {
  const { clock, pass } = handClock();
  const shown: string[] = [];
  const dwell = showAfterTheLastOfferRests('', REST, (id) => shown.push(id), clock);
  for (const id of ['a', '', 'b', '', 'c']) {
    dwell.offer(id);
    pass(REST / 3);
  }
  pass(REST);
  assert.deepEqual(shown, ['c']);
});

test('leaving a subject and re-entering it before the rest elapses is no change at all', () => {
  const { clock, pass, waiting, started } = handClock();
  const shown: string[] = [];
  const dwell = showAfterTheLastOfferRests('', REST, (id) => shown.push(id), clock);
  dwell.offer('wire');
  pass(REST);
  assert.deepEqual(shown, ['wire']);
  const timersBeforeTheCrossing = started.length;
  dwell.offer('');
  dwell.offer('wire');
  assert.equal(waiting.size, 0, 'the crossing leaves no timer running');
  assert.equal(started.length, timersBeforeTheCrossing + 1, 'only the leave started a timer, and re-entering dropped it');
  pass(REST * 4);
  assert.deepEqual(shown, ['wire'], 'nothing was shown again');
});

test('a subject shown at once drops whatever was waiting', () => {
  const { clock, pass } = handClock();
  const shown: string[] = [];
  const dwell = showAfterTheLastOfferRests('a', REST, (id) => shown.push(id), clock);
  dwell.offer('b');
  dwell.showNow('');
  pass(REST * 2);
  assert.deepEqual(shown, []);
  assert.equal(dwell.shown(), '');
});
