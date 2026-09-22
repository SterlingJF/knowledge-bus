import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const config = resolve(import.meta.dirname, 'playwright.config.ts');

const lanes = await import('./lanes.ts');

const titlesPlaywrightDiscovers = (lane) => {
  const listed = execFileSync('pnpm', ['exec', 'playwright', 'test', '--config', config, '--list', '--reporter=json'], {
    cwd: root,
    encoding: 'utf8',
    env: { ...process.env, KB_EXPLORER_LANE: lane },
    maxBuffer: 64 * 1024 * 1024,
  });
  const found = [];
  const walk = (suite) => {
    for (const nested of suite.suites ?? []) walk(nested);
    for (const spec of suite.specs ?? []) found.push(spec.title);
  };
  for (const suite of JSON.parse(listed).suites) walk(suite);
  return found;
};

const discovered = [...titlesPlaywrightDiscovers('parallel'), ...titlesPlaywrightDiscovers('exclusive')];

test('every browser test states a lane, and every lane entry names a test that exists', () => {
  const claimed = lanes.everyTitleALaneClaims();
  const unstated = discovered.filter((title) => !claimed.includes(title));
  const stale = claimed.filter((title) => !discovered.includes(title));
  assert.deepEqual(unstated, [], 'a test with no lane would run under whatever contention the parallel lane happens to give it');
  assert.deepEqual(stale, [], 'a lane entry naming no test hides a rename behind a passing run');
});

test('the lanes partition the suite, so no test is run twice or dropped', () => {
  const claimed = lanes.everyTitleALaneClaims();
  assert.equal(new Set(claimed).size, claimed.length, 'a title claimed by two lanes would run twice');
  assert.equal(discovered.length, claimed.length);
  assert.deepEqual([...discovered].sort(), [...claimed].sort());
});

test('the lane that lets workers contend never carries a test observed to fail while they do', () => {
  for (const title of lanes.testsObservedToFailWhileWorkersContend)
    assert.ok(!lanes.testsObservedToPassWhileWorkersContend.includes(title), `${title} is claimed by both lanes`);
  assert.deepEqual(titlesPlaywrightDiscovers('exclusive'), [...lanes.testsObservedToFailWhileWorkersContend]);
});

test('an unknown or unset lane refuses rather than choosing one', () => {
  assert.throws(() => lanes.laneNamed(undefined), /KB_EXPLORER_LANE/);
  assert.throws(() => lanes.laneNamed(''), /KB_EXPLORER_LANE/);
  assert.throws(() => lanes.laneNamed('fast'), /KB_EXPLORER_LANE/);
});

test('a lane cannot take workers without the parallelism setting that makes them meaningful', () => {
  const parallel = lanes.laneOptions(lanes.LANES.parallel);
  const exclusive = lanes.laneOptions(lanes.LANES.exclusive);
  assert.equal(parallel.fullyParallel, true);
  assert.notEqual(parallel.workers, 1);
  assert.equal(exclusive.fullyParallel, false);
  assert.equal(exclusive.workers, 1);
});
