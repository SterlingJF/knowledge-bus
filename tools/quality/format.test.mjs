import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, copyFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const prettier = path.join(root, 'node_modules/prettier/bin/prettier.cjs');
const markdownlint = path.join(root, 'node_modules/markdownlint-cli2/markdownlint-cli2-bin.mjs');
const ruff = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/ruff.exe' : 'bin/ruff');

test('Markdownlint owns emphasis and indentation; Prettier skips Markdown', () => {
  const cwd = mkdtempSync(path.join(tmpdir(), 'knowledge-bus-quality-'));
  const run = (command, args) => {
    const result = spawnSync(command, args, { cwd, encoding: 'utf8' });
    assert.ifError(result.error);
    return result;
  };
  const node = (...args) => run(process.execPath, args);
  try {
    for (const config of ['.prettierignore', '.markdownlint-cli2.jsonc']) {
      copyFileSync(path.join(root, config), path.join(cwd, config));
    }
    // Ruff's root config is authoritative; do not copy the uv workspace.
    const pythonArgs = ['--config', path.join(root, 'pyproject.toml')];
    const markdown = '# Example\n\n_Italic_ and *already preferred*.\n\n- item\n    - child\n\n| A | B |\n| --- | --- |\n| one | two |\n';
    const python = 'import os\n\nx= [1,2,3]\n';
    writeFileSync(path.join(cwd, 'sample.md'), markdown);
    writeFileSync(path.join(cwd, 'sample.py'), python);
    for (const folder of ['references', 'runtime']) {
      mkdirSync(path.join(cwd, 'skills/example', folder), { recursive: true });
      writeFileSync(path.join(cwd, 'skills/example', folder, 'sample.md'), markdown);
      writeFileSync(path.join(cwd, 'skills/example', folder, 'sample.py'), python);
    }
    assert.equal(node(prettier, '--check', '**/*.md').status, 0);
    assert.equal(node(prettier, '--write', 'sample.md').status, 0);
    assert.equal(readFileSync(path.join(cwd, 'sample.md'), 'utf8'), markdown);
    assert.equal(run(ruff, ['format', '--check', ...pythonArgs, '.']).status, 1);
    const lint = node(markdownlint, '**/*.md');
    assert.equal(lint.status, 1);
    assert.match(lint.stdout + lint.stderr, /MD049/);
    assert.match(lint.stdout + lint.stderr, /MD007/);
    run(ruff, ['check', ...pythonArgs, '.']);
    assert.equal(readFileSync(path.join(cwd, 'sample.md'), 'utf8'), markdown);
    assert.equal(readFileSync(path.join(cwd, 'sample.py'), 'utf8'), python);
    assert.equal(run(ruff, ['check', '--fix', ...pythonArgs, '.']).status, 0);
    assert.equal(node(markdownlint, '--fix', '**/*.md').status, 0);
    assert.equal(run(ruff, ['format', ...pythonArgs, '.']).status, 0);
    assert.equal(node(prettier, '--write', '**/*.md').status, 0);
    const formatted = readFileSync(path.join(cwd, 'sample.md'), 'utf8');
    assert.match(formatted, /\*Italic\* and \*already preferred\*/);
    assert.match(formatted, /\n  - child\n/);
    assert.ok(formatted.includes('| A | B |\n| --- | --- |\n| one | two |'));
    assert.equal(node(markdownlint, '--fix', '**/*.md').status, 0);
    assert.equal(readFileSync(path.join(cwd, 'sample.md'), 'utf8'), formatted);
    assert.equal(node(prettier, '--check', '**/*.md').status, 0);
    assert.equal(run(ruff, ['format', '--check', ...pythonArgs, '.']).status, 0);
    for (const folder of ['references', 'runtime']) {
      assert.equal(readFileSync(path.join(cwd, 'skills/example', folder, 'sample.md'), 'utf8'), markdown);
      assert.equal(readFileSync(path.join(cwd, 'skills/example', folder, 'sample.py'), 'utf8'), python);
    }
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
});

test('formatting commands do not include Markdown or Prettier', () => {
  const { scripts } = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'));
  assert.equal(scripts.format, 'pnpm run format:python');
  assert.equal(scripts['check:format'], 'pnpm run check:format:python');
  assert.equal(scripts['format:markdown'], undefined);
  assert.equal(scripts['check:format:markdown'], undefined);
});
