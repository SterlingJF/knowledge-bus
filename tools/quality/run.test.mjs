import assert from 'node:assert/strict';
import test from 'node:test';
import { runScripts } from './run.mjs';

test('attempts later scripts and preserves earlier failures', () => {
  const visited = [];
  assert.equal(runScripts(['fix:python', 'fix:markdown', 'format'], (_cmd, args) => {
    visited.push(args.at(-1));
    return { status: visited.length === 1 ? 1 : 0 };
  }), 1);
  assert.deepEqual(visited, ['fix:python', 'fix:markdown', 'format']);
});

test('succeeds only when every script succeeds', () => {
  assert.equal(runScripts(['python', 'markdown'], () => ({ status: 0 })), 0);
  assert.equal(runScripts([], () => ({ status: 0 })), 1);
});

test('stops on interruption instead of starting more modifications', () => {
  let calls = 0;
  assert.equal(runScripts(['first', 'second'], () => {
    calls += 1;
    return { status: null, signal: 'SIGINT' };
  }), 1);
  assert.equal(calls, 1);
});
