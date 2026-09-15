import { spawn, spawnSync } from 'node:child_process';
import { copyFileSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

function command(executable, args, options = {}) {
  const result = spawnSync(executable, args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, ...options });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(result.stderr || `${executable} failed (${result.status}).`);
  return result.stdout;
}

function git(root, args, env = process.env) {
  return command('git', ['-C', root, ...args], { env });
}

export function pushTips(input) {
  const tips = new Set();
  for (const line of input.trim().split('\n').filter(Boolean)) {
    const fields = line.trim().split(/\s+/);
    if (fields.length !== 4 || !/^[a-f0-9]{40,64}$/.test(fields[1])) {
      throw new Error('Expected Git pre-push input: local-ref local-oid remote-ref remote-oid.');
    }
    if (!/^0+$/.test(fields[1]) && fields[2].startsWith('refs/heads/')) tips.add(fields[1]);
  }
  return [...tips];
}

export function exportSnapshot(root, base, revision) {
  const snapshot = path.join(realpathSync(base), 'source');
  mkdirSync(snapshot);
  const index = path.join(base, 'index');
  const env = { ...process.env, GIT_INDEX_FILE: index, GIT_OPTIONAL_LOCKS: '0' };
  if (revision) {
    git(root, ['read-tree', `${revision}^{commit}`], env);
  } else {
    const source = git(root, ['rev-parse', '--path-format=absolute', '--git-path', 'index']).trim();
    if (existsSync(source)) copyFileSync(source, index);
    else git(root, ['read-tree', '--empty'], env);
    // Flatten a split index while Git can still resolve its shared index in this repository.
    git(root, ['update-index', '--no-split-index'], env);
  }
  const entries = git(root, ['ls-files', '--stage', '-z'], env).split('\0').filter(Boolean);
  for (const entry of entries) {
    const [header, ...nameParts] = entry.split('\t');
    const [mode, , stage] = header.split(' ');
    const name = nameParts.join('\t');
    if (stage !== '0') throw new Error('Resolve merge conflicts before checking a snapshot.');
    if (mode === '160000') throw new Error(`Snapshot checks do not support submodules: ${name}`);
    if (/^(?:\.git|\.venv|node_modules)(?:\/|$)/.test(name)) {
      throw new Error(`Reserved snapshot path is tracked: ${name}`);
    }
  }
  git(root, ['checkout-index', '--all', '--ignore-skip-worktree-bits', `--prefix=${snapshot}/`], env);
  for (const entry of entries) {
    const name = entry.slice(entry.indexOf('\t') + 1);
    const target = path.join(snapshot, name);
    if (lstatSync(target).isSymbolicLink()) {
      const resolved = realpathSync(target);
      if (!resolved.startsWith(snapshot + path.sep)) throw new Error(`Symlink escapes snapshot: ${name}`);
    }
  }
  return snapshot;
}

export function prepareTools(root, snapshot, base) {
  if (!existsSync(path.join(snapshot, 'pnpm-workspace.yaml'))) {
    throw new Error('The snapshot must include pnpm-workspace.yaml.');
  }
  if (!existsSync(path.join(root, 'node_modules/.pnpm/lock.yaml'))) {
    throw new Error('Node dependencies are missing. Run pnpm install --frozen-lockfile first.');
  }
  for (const file of ['pnpm-lock.yaml', 'uv.lock']) {
    if (!readFileSync(path.join(root, file)).equals(readFileSync(path.join(snapshot, file)))) {
      throw new Error(`${file} differs from the checkout. Set up dependencies for this snapshot before checking it.`);
    }
  }
  const python = path.join(root, '.venv/bin/python');
  if (!existsSync(python)) throw new Error('Python dependencies are missing. Run uv sync --locked first.');
  command(python, ['-I', '-B', fileURLToPath(new URL('./snapshot_env.py', import.meta.url)), snapshot, root], {
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
  });
  symlinkSync(path.join(root, 'node_modules'), path.join(snapshot, 'node_modules'), 'dir');
  const env = { ...process.env };
  for (const key of Object.keys(env)) {
    if (key.startsWith('GIT_') || key.startsWith('PYTHON') || [
      'UV_PROJECT', 'UV_PROJECT_ENVIRONMENT', 'UV_WORKING_DIRECTORY',
      'UV_CONFIG_FILE', 'UV_PYTHON', 'UV_FROZEN', 'UV_NO_SYNC',
    ].includes(key)) delete env[key];
  }
  return {
    ...env,
    PATH: `${snapshot}/.venv/bin${path.delimiter}${env.PATH}`,
    VIRTUAL_ENV: `${snapshot}/.venv`,
    UV_PROJECT_ENVIRONMENT: `${snapshot}/.venv`,
    UV_NO_SYNC: '1',
    UV_PYTHON_DOWNLOADS: 'never',
    PYTHONDONTWRITEBYTECODE: '1',
    PYTHONNOUSERSITE: '1',
    pnpm_config_verify_deps_before_run: '',
    RUFF_CACHE_DIR: path.join(base, 'ruff-cache'),
    KNOWLEDGE_BUS_CACHE_DIR: path.join(base, 'runtime-cache'),
    TMPDIR: base,
  };
}

export async function runCheck(snapshot, script, env) {
  return new Promise((resolve, reject) => {
    const child = spawn('pnpm', ['run', script], { cwd: snapshot, env, stdio: 'inherit', detached: true });
    let interrupted = false;
    let timer;
    const stop = (signal) => {
      interrupted = true;
      try { process.kill(-child.pid, signal); } catch { /* Already exited. */ }
      timer = setTimeout(() => {
        try { process.kill(-child.pid, 'SIGKILL'); } catch { /* Already exited. */ }
      }, 1000);
    };
    const onInt = () => stop('SIGINT');
    const onTerm = () => stop('SIGTERM');
    process.on('SIGINT', onInt);
    process.on('SIGTERM', onTerm);
    const cleanup = () => {
      clearTimeout(timer);
      process.off('SIGINT', onInt);
      process.off('SIGTERM', onTerm);
    };
    child.once('error', (error) => { cleanup(); reject(error); });
    child.once('close', (code) => {
      if (interrupted) {
        try { process.kill(-child.pid, 'SIGKILL'); } catch { /* Already exited. */ }
      }
      cleanup();
      resolve(interrupted ? 1 : code ?? 1);
    });
  });
}

export async function checkSnapshots({ root, mode, input = '', prepare = prepareTools, run = runCheck }) {
  if (!['staged', 'push'].includes(mode)) throw new Error('Choose staged or push snapshot checks.');
  const revisions = mode === 'staged' ? [undefined] : pushTips(input);
  for (const revision of revisions) {
    const base = mkdtempSync(path.join(tmpdir(), 'knowledge-bus-snapshot-'));
    try {
      const snapshot = exportSnapshot(root, base, revision);
      console.log(`Checking ${revision ? `outgoing commit ${revision}` : 'staged content'} (isolated snapshot).`);
      const env = prepare(root, snapshot, base);
      if (await run(snapshot, mode === 'staged' ? 'check:fast' : 'check', env) !== 0) return 1;
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  }
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const root = git(process.cwd(), ['rev-parse', '--show-toplevel']).trim();
    process.exitCode = await checkSnapshots({
      root, mode: process.argv[2], input: process.argv[2] === 'push' ? readFileSync(0, 'utf8') : '',
    });
  } catch (error) {
    console.error(`Snapshot check failed: ${error.message}`);
    process.exitCode = 1;
  }
}
