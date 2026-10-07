import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const script = resolve(dirname(fileURLToPath(import.meta.url)), 'sync-regions.mjs');

const moduleReadme = `# alpha

## Layout

\`\`\`text
alpha/
└── file
\`\`\`

### Notes

Kept with Layout.

## Commands

Not copied.
`;

const region = (ref, body = '') => `<!-- BEGIN AUTO-GENERATED ${ref} -->\n${body}<!-- END AUTO-GENERATED ${ref} -->\n`;

function workspace(files) {
  const dir = mkdtempSync(join(tmpdir(), 'sync-regions-'));
  for (const [path, contents] of Object.entries(files)) {
    mkdirSync(dirname(join(dir, path)), { recursive: true });
    writeFileSync(join(dir, path), contents);
  }
  return dir;
}

function run(dir, ...args) {
  const result = spawnSync(process.execPath, [script, 'README.md', ...args], {
    cwd: dir,
    encoding: 'utf8',
  });
  return {
    status: result.status,
    output: result.stdout + result.stderr,
    readme: readFileSync(join(dir, 'README.md'), 'utf8'),
  };
}

test('fills a region from the file and heading its marker names', () => {
  const dir = workspace({
    'alpha/README.md': moduleReadme,
    'README.md': `# Root\n\n${region('alpha/README.md#layout', 'old\n')}\nAfter.\n`,
  });
  const { status, readme } = run(dir);
  assert.equal(status, 0);
  assert.equal(
    readme,
    `# Root\n\n${region('alpha/README.md#layout', '\n```text\nalpha/\n└── file\n```\n\n### Notes\n\nKept with Layout.\n\n')}\nAfter.\n`,
  );
});

test('fills every region in one file', () => {
  const dir = workspace({
    'alpha/README.md': moduleReadme,
    'beta/README.md': '# beta\n\n## Layout\n\nbeta map\n',
    'README.md': `${region('alpha/README.md#layout')}\n${region('beta/README.md#layout')}`,
  });
  const { status, readme } = run(dir);
  assert.equal(status, 0);
  assert.match(readme, /alpha\/\n└── file/);
  assert.match(readme, /\nbeta map\n/);
});

test('is idempotent', () => {
  const dir = workspace({
    'alpha/README.md': moduleReadme,
    'README.md': region('alpha/README.md#layout'),
  });
  const first = run(dir).readme;
  assert.equal(run(dir).readme, first);
});

test('check passes when every region is current', () => {
  const dir = workspace({
    'alpha/README.md': moduleReadme,
    'README.md': region('alpha/README.md#layout'),
  });
  run(dir);
  assert.equal(run(dir, '--check').status, 0);
});

test('check fails on drift and leaves the file untouched', () => {
  const stale = region('alpha/README.md#layout', 'old\n');
  const dir = workspace({
    'alpha/README.md': moduleReadme,
    'README.md': stale,
  });
  const { status, output, readme } = run(dir, '--check');
  assert.equal(status, 1);
  assert.match(output, /stale: README\.md alpha\/README\.md#layout/);
  assert.equal(readme, stale);
});

test('ignores headings inside backtick and tilde fences', () => {
  const dir = workspace({
    'alpha/README.md': '## Layout\n\n```text\n## Not a heading\n```\n\n~~~text\n## Also not\n~~~\n\nend\n',
    'README.md': region('alpha/README.md#layout'),
  });
  const { status, readme } = run(dir);
  assert.equal(status, 0);
  assert.match(readme, /## Also not\n~~~\n\nend\n/);
});

test('fails when the source file is missing', () => {
  const dir = workspace({ 'README.md': region('gone/README.md#layout') });
  const { status, output } = run(dir);
  assert.equal(status, 1);
  assert.match(output, /gone\/README\.md/);
});

test('fails when the heading is missing', () => {
  const dir = workspace({
    'alpha/README.md': '# alpha\n',
    'README.md': region('alpha/README.md#layout'),
  });
  const { status, output } = run(dir);
  assert.equal(status, 1);
  assert.match(output, /#layout not found/);
});

test('fails when a region has no end marker', () => {
  const dir = workspace({
    'alpha/README.md': moduleReadme,
    'README.md': '<!-- BEGIN AUTO-GENERATED alpha/README.md#layout -->\n',
  });
  const { status, output } = run(dir);
  assert.equal(status, 1);
  assert.match(output, /unmatched/);
});

test('fails when a file has no regions', () => {
  const dir = workspace({ 'README.md': '# Root\n' });
  const { status, output } = run(dir);
  assert.equal(status, 1);
  assert.match(output, /no regions/);
});
