import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { checkSnapshots, exportSnapshot, prepareTools, pushTips, runPushChecks } from './snapshot.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
const zero = '0'.repeat(40);
function run(cwd, command, args, extra = {}) {
  const result = spawnSync(command, args, { cwd, encoding: 'utf8', ...extra });
  assert.ifError(result.error);
  return result;
}
function git(cwd, ...args) {
  const result = run(cwd, 'git', args);
  assert.equal(result.status, 0, result.stderr);
  return result.stdout.trim();
}
function write(cwd, file, contents) {
  mkdirSync(path.dirname(path.join(cwd, file)), { recursive: true });
  writeFileSync(path.join(cwd, file), contents);
}
function repository(t) {
  const cwd = mkdtempSync(path.join(tmpdir(), 'knowledge-bus-hooks-test-'));
  t.after(() => rmSync(cwd, { recursive: true, force: true }));
  git(cwd, 'init', '-q', '--initial-branch=main');
  git(cwd, 'config', 'user.name', 'Hook Test');
  git(cwd, 'config', 'user.email', 'hook@example.invalid');
  git(cwd, 'config', 'commit.gpgsign', 'false');
  write(cwd, '.gitignore', '.venv\nnode_modules\n.husky/_/\nremote.git/\n');
  write(cwd, 'value.txt', 'valid');
  git(cwd, 'add', '.');
  git(cwd, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Fixture');
  return cwd;
}
function state(cwd) {
  return {
    index: readFileSync(path.join(cwd, '.git/index')).toString('hex'),
    tracked: git(cwd, 'diff', '--binary'),
    staged: git(cwd, 'diff', '--cached', '--binary'),
  };
}

test('staged snapshots preserve partial staging, additions, deletions and renames', async (t) => {
  const cwd = repository(t);
  write(cwd, 'delete.txt', 'delete');
  write(cwd, 'rename.txt', 'rename');
  git(cwd, 'add', '.');
  git(cwd, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'More files');
  git(cwd, 'mv', 'rename.txt', 'renamed.txt');
  git(cwd, 'rm', 'delete.txt');
  write(cwd, 'value.txt', 'staged');
  write(cwd, 'added.txt', 'added');
  git(cwd, 'add', '.');
  write(cwd, 'value.txt', 'unstaged');
  write(cwd, 'untracked.txt', 'untracked');
  const before = state(cwd);
  let exported;
  const code = await checkSnapshots({ root: cwd, mode: 'staged', prepare: () => ({}), run: (snapshot, script) => {
    exported = snapshot;
    assert.equal(script, 'check:fast');
    assert.equal(readFileSync(path.join(snapshot, 'value.txt'), 'utf8'), 'staged');
    assert.equal(readFileSync(path.join(snapshot, 'added.txt'), 'utf8'), 'added');
    assert.ok(existsSync(path.join(snapshot, 'renamed.txt')));
    for (const file of ['delete.txt', 'rename.txt', 'untracked.txt']) assert.ok(!existsSync(path.join(snapshot, file)));
    return 0;
  } });
  assert.equal(code, 0);
  assert.ok(!existsSync(exported));
  assert.deepEqual(state(cwd), before);
  assert.equal(readFileSync(path.join(cwd, 'untracked.txt'), 'utf8'), 'untracked');
});

test('failed checks and setup exceptions clean snapshots without touching the index', async (t) => {
  const cwd = repository(t);
  const before = state(cwd);
  let exported;
  assert.equal(await checkSnapshots({ root: cwd, mode: 'staged', prepare: () => ({}), run: (snapshot) => {
    exported = snapshot;
    return 1;
  } }), 1);
  assert.ok(!existsSync(exported));
  await assert.rejects(checkSnapshots({ root: cwd, mode: 'staged', prepare: (_root, snapshot) => {
    exported = snapshot;
    throw new Error('Missing dependencies');
  } }), /Missing dependencies/);
  assert.ok(!existsSync(exported));
  assert.deepEqual(state(cwd), before);
});

test('pre-push selects unique outgoing branch tips, not HEAD, tags or deletions', async (t) => {
  const cwd = repository(t);
  const first = git(cwd, 'rev-parse', 'HEAD');
  write(cwd, 'value.txt', 'second');
  git(cwd, 'add', '.');
  git(cwd, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Second');
  const second = git(cwd, 'rev-parse', 'HEAD');
  write(cwd, 'value.txt', 'working');
  const input = `refs/heads/one ${first} refs/heads/one ${zero}\nHEAD ${second} refs/heads/two ${first}\nHEAD ${first} refs/heads/copy ${zero}\nrefs/tags/v1 ${second} refs/tags/v1 ${zero}\n(delete) ${zero} refs/heads/gone ${first}\n`;
  assert.deepEqual(pushTips(input), [first, second]);
  assert.deepEqual(pushTips(''), []);
  assert.throws(() => pushTips('bad input'), /Expected Git/);
  const seen = [];
  assert.equal(await checkSnapshots({ root: cwd, mode: 'push', input, prepare: () => ({}), run: (snapshot, script) => {
    seen.push([readFileSync(path.join(snapshot, 'value.txt'), 'utf8'), script]);
    return 0;
  } }), 0);
  const scripts = ['test:explorer:unit', 'check:fast', 'check:plugins', 'test', 'test:explorer:adapter', 'build:explorer', 'render:explorer', 'test:explorer:browser', 'check:explorer:artifacts'];
  assert.deepEqual(seen, ['valid', 'second'].flatMap((value) => scripts.map((script) => [value, script])));
});

test('pre-push overlaps unit tests, waits for bundle readers, and reports failures from both lanes', async () => {
  const seen = [];
  let finishUnit;
  const unit = new Promise((resolve) => { finishUnit = resolve; });
  const pending = runPushChecks('snapshot', {}, (_snapshot, script) => {
    seen.push(script);
    if (script === 'test:explorer:unit') return unit;
    return 0;
  });
  let settled = false;
  void pending.then(() => { settled = true; });
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(seen, ['test:explorer:unit', 'check:fast', 'check:plugins', 'test', 'test:explorer:adapter', 'build:explorer', 'render:explorer', 'test:explorer:browser', 'check:explorer:artifacts']);
  assert.equal(settled, false);
  finishUnit(1);
  assert.equal(await pending, 1);
  assert.equal(await runPushChecks('snapshot', {}, (_snapshot, script) => script === 'check:plugins' ? 1 : 0), 1);
  const interrupted = [];
  assert.equal(await runPushChecks('snapshot', {}, (_snapshot, script) => {
    interrupted.push(script);
    return script === 'check:fast' ? 143 : 0;
  }), 1);
  assert.deepEqual(interrupted, ['test:explorer:unit', 'check:fast']);
});

test('escaping symlinks and unresolved indexes fail closed', async (t) => {
  const cwd = repository(t);
  symlinkSync(tmpdir(), path.join(cwd, 'outside'));
  git(cwd, 'add', 'outside');
  await assert.rejects(checkSnapshots({ root: cwd, mode: 'staged', prepare: () => ({}) }), /Symlink escapes/);
  git(cwd, 'rm', '--cached', 'outside');
  const oid = git(cwd, 'rev-parse', 'HEAD:value.txt');
  const result = run(cwd, 'git', ['update-index', '--index-info'], {
    input: `0 ${zero}\tvalue.txt\n100644 ${oid} 1\tvalue.txt\n100644 ${oid} 2\tvalue.txt\n`,
  });
  assert.equal(result.status, 0, result.stderr);
  await assert.rejects(checkSnapshots({ root: cwd, mode: 'staged', prepare: () => ({}) }), /Resolve merge conflicts/);
});

function hookedRepository(t) {
  const cwd = repository(t);
  for (const file of ['tools/quality/snapshot.mjs', 'tools/quality/snapshot_env.py', '.husky/pre-commit', '.husky/pre-push', 'uv.lock', 'pnpm-lock.yaml', 'pnpm-workspace.yaml', 'checker/pyproject.toml']) {
    write(cwd, file, readFileSync(path.join(root, file)));
  }
  write(cwd, 'checker/src/kbp_conform/__init__.py', 'MARKER = "snapshot"\n');
  write(cwd, 'package.json', JSON.stringify({ ...JSON.parse(readFileSync(path.join(root, 'package.json'))), scripts: {
    'check:staged': 'node tools/quality/snapshot.mjs staged',
    'check:push': 'node tools/quality/snapshot.mjs push',
    'check:fast': 'node verify.mjs',
    'check:plugins': 'node verify.mjs',
    test: 'node verify.mjs',
    'test:explorer:unit': 'node verify.mjs',
    'test:explorer:adapter': 'node verify.mjs',
    'build:explorer': 'node verify.mjs',
    'render:explorer': 'node verify.mjs',
    'test:explorer:browser': 'node verify.mjs',
    'check:explorer:artifacts': 'node verify.mjs',
  } }));
  write(cwd, 'justfile', 'check-staged:\n    node tools/quality/snapshot.mjs staged\ncheck-push:\n    node tools/quality/snapshot.mjs push\n');
  write(cwd, 'verify.mjs', `import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
assert.equal(readFileSync('value.txt', 'utf8'), 'valid');
const p = spawnSync('.venv/bin/python', ['-c', 'import kbp_conform; from pathlib import Path; assert kbp_conform.MARKER == "snapshot"; assert Path(kbp_conform.__file__).is_relative_to(Path.cwd())'], {encoding:'utf8'});
assert.equal(p.status, 0, p.stderr);
`);
  symlinkSync(path.join(root, '.venv'), path.join(cwd, '.venv'), 'dir');
  symlinkSync(path.join(root, 'node_modules'), path.join(cwd, 'node_modules'), 'dir');
  git(cwd, 'add', '.');
  git(cwd, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Hook tooling');
  const installed = run(cwd, process.execPath, [path.join(root, 'node_modules/husky/bin.js')]);
  assert.equal(installed.status, 0, installed.stderr);
  return cwd;
}

test('real Husky pre-commit checks staged content and imports snapshot Python', (t) => {
  const cwd = hookedRepository(t);
  write(cwd, 'other.txt', 'staged change');
  git(cwd, 'add', 'other.txt');
  write(cwd, 'value.txt', 'invalid unstaged edit');
  write(cwd, 'checker/src/kbp_conform/__init__.py', 'MARKER = "working tree"\n');
  const committed = run(cwd, 'git', ['commit', '-qm', 'Valid staged snapshot']);
  assert.equal(committed.status, 0, committed.stdout + committed.stderr);
  assert.equal(readFileSync(path.join(cwd, 'value.txt'), 'utf8'), 'invalid unstaged edit');
  git(cwd, 'add', 'value.txt');
  write(cwd, 'value.txt', 'valid');
  const before = state(cwd);
  const rejected = run(cwd, 'git', ['commit', '-qm', 'Invalid staged snapshot']);
  assert.notEqual(rejected.status, 0, rejected.stdout + rejected.stderr);
  // Git itself may refresh index caches while attempting a commit.
  const after = state(cwd);
  assert.equal(after.staged, before.staged);
  assert.equal(after.tracked, before.tracked);
});

test('split and alternate indexes export their own staged contents', async (t) => {
  const cwd = repository(t);
  git(cwd, 'update-index', '--split-index');
  const before = state(cwd);
  assert.equal(await checkSnapshots({ root: cwd, mode: 'staged', prepare: () => ({}), run: () => 0 }), 0);
  assert.deepEqual(state(cwd), before);
  git(cwd, 'update-index', '--no-split-index');
  const alternate = path.join(cwd, '.git/alternate-index');
  copyFileSync(path.join(cwd, '.git/index'), alternate);
  write(cwd, 'value.txt', 'alternate');
  const env = { ...process.env, GIT_INDEX_FILE: alternate };
  const result = run(cwd, 'git', ['add', 'value.txt'], { env });
  assert.equal(result.status, 0, result.stderr);
  const previous = process.env.GIT_INDEX_FILE;
  try {
    process.env.GIT_INDEX_FILE = alternate;
    assert.equal(await checkSnapshots({ root: cwd, mode: 'staged', prepare: () => ({}), run: (snapshot) => {
      assert.equal(readFileSync(path.join(snapshot, 'value.txt'), 'utf8'), 'alternate');
      return 0;
    } }), 0);
  } finally {
    if (previous === undefined) delete process.env.GIT_INDEX_FILE;
    else process.env.GIT_INDEX_FILE = previous;
  }
});

test('real Husky pre-push checks the pushed commit and blocks invalid tips', (t) => {
  const cwd = hookedRepository(t);
  const remote = path.join(cwd, 'remote.git');
  git(cwd, 'init', '--bare', remote);
  git(cwd, 'remote', 'add', 'origin', remote);
  write(cwd, 'value.txt', 'invalid working tree');
  let result = run(cwd, 'git', ['push', 'origin', 'main']);
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const previous = git(cwd, 'rev-parse', 'HEAD');
  git(cwd, 'add', 'value.txt');
  git(cwd, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Invalid tip');
  write(cwd, 'value.txt', 'valid');
  result = run(cwd, 'git', ['push', 'origin', 'main']);
  assert.notEqual(result.status, 0);
  assert.equal(git(remote, 'rev-parse', 'refs/heads/main'), previous);
});

test('tool preparation rejects stale locks and never falls back to the editable checker', (t) => {
  const cwd = hookedRepository(t);
  const base = mkdtempSync(path.join(tmpdir(), 'knowledge-bus-env-test-'));
  t.after(() => rmSync(base, { recursive: true, force: true }));
  const snapshot = exportSnapshot(cwd, base);
  const env = prepareTools(cwd, snapshot, base);
  const ruff = run(snapshot, '.venv/bin/ruff', ['--version'], { env, timeout: 5000 });
  assert.equal(ruff.status, 0, ruff.stderr);
  assert.match(ruff.stdout, /^ruff /);
  rmSync(path.join(snapshot, 'checker/src/kbp_conform'), { recursive: true });
  const result = run(snapshot, '.venv/bin/python', ['-c', 'import kbp_conform'], { env });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /No module named 'kbp_conform'/);
  const changedLock = readFileSync(path.join(cwd, 'pnpm-lock.yaml'), 'utf8').replace('husky:', 'unexpected-package:');
  write(cwd, 'pnpm-lock.yaml', changedLock);
  write(snapshot, 'pnpm-lock.yaml', changedLock);
  assert.throws(() => prepareTools(cwd, snapshot, base), /Node dependencies are stale/);
  write(snapshot, 'uv.lock', 'different');
  assert.throws(() => prepareTools(cwd, snapshot, base), /uv.lock differs/);
});

test('interruption stops checks, cleans the snapshot and preserves staged content', async (t) => {
  const cwd = hookedRepository(t);
  write(cwd, 'verify.mjs', `import { writeFileSync } from 'node:fs';
writeFileSync(${JSON.stringify(path.join(cwd, 'started'))}, process.cwd());
setInterval(() => {}, 1000);
`);
  git(cwd, 'add', 'verify.mjs');
  const before = state(cwd);
  const child = spawn(process.execPath, ['tools/quality/snapshot.mjs', 'staged'], { cwd, stdio: 'ignore' });
  t.after(() => { if (child.exitCode === null) child.kill('SIGKILL'); });
  const done = new Promise((resolve) => child.once('exit', resolve));
  const deadline = Date.now() + 15000;
  while (!existsSync(path.join(cwd, 'started')) && Date.now() < deadline && child.exitCode === null) {
    await new Promise((resolve) => setTimeout(resolve, 30));
  }
  assert.ok(existsSync(path.join(cwd, 'started')), 'snapshot command started');
  const snapshot = readFileSync(path.join(cwd, 'started'), 'utf8');
  child.kill('SIGTERM');
  assert.notEqual(await done, 0);
  assert.ok(!existsSync(snapshot));
  assert.deepEqual(state(cwd), before);
});

test('pre-push interruption stops both lanes and cleans the snapshot', async (t) => {
  const cwd = hookedRepository(t);
  write(cwd, 'verify.mjs', `import { writeFileSync } from 'node:fs';
writeFileSync(${JSON.stringify(path.join(cwd, 'started-'))} + process.env.npm_lifecycle_event, process.pid + '\\n' + process.cwd());
setInterval(() => {}, 1000);
`);
  git(cwd, 'add', 'verify.mjs');
  git(cwd, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Long running checks');
  const before = state(cwd);
  const oid = git(cwd, 'rev-parse', 'HEAD');
  const child = spawn(process.execPath, ['tools/quality/snapshot.mjs', 'push'], { cwd, stdio: ['pipe', 'ignore', 'ignore'] });
  t.after(() => { if (child.exitCode === null) child.kill('SIGKILL'); });
  child.stdin.end(`refs/heads/main ${oid} refs/heads/main ${zero}\n`);
  const done = new Promise((resolve) => child.once('exit', resolve));
  const markers = ['test:explorer:unit', 'check:fast'].map((script) => path.join(cwd, `started-${script}`));
  const deadline = Date.now() + 15000;
  while (!markers.every(existsSync) && Date.now() < deadline && child.exitCode === null)
    await new Promise((resolve) => setTimeout(resolve, 30));
  assert.ok(markers.every(existsSync), 'both concurrent checks started');
  const running = markers.map((marker) => {
    const [pid, snapshot] = readFileSync(marker, 'utf8').split('\n');
    return { pid: Number(pid), snapshot };
  });
  child.kill('SIGTERM');
  assert.notEqual(await done, 0);
  assert.ok(!existsSync(path.join(cwd, 'started-check:plugins')));
  assert.ok(running.every(({ snapshot }) => !existsSync(snapshot)));
  const stopped = (pid) => {
    try { process.kill(pid, 0); return false; }
    catch (error) { if (error.code === 'ESRCH') return true; throw error; }
  };
  const stopDeadline = Date.now() + 3000;
  while (running.some(({ pid }) => !stopped(pid)) && Date.now() < stopDeadline)
    await new Promise((resolve) => setTimeout(resolve, 30));
  assert.ok(running.every(({ pid }) => stopped(pid)), 'both check processes stopped');
  assert.deepEqual(state(cwd), before);
});
