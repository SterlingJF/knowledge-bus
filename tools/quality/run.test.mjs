import assert from 'node:assert/strict';
import test from 'node:test';
import { runScripts } from './run.mjs';

test('executes the package manager directly, including native executables', () => {
  const previous = process.env.npm_execpath;
  process.env.npm_execpath = '/example/pnpm';
  try {
    assert.equal(runScripts(['lint'], (command, args) => {
      assert.equal(command, '/example/pnpm');
      assert.deepEqual(args, ['run', 'lint']);
      return { status: 0 };
    }), 0);
  } finally {
    if (previous === undefined) delete process.env.npm_execpath;
    else process.env.npm_execpath = previous;
  }
});

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
