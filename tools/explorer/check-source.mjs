import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { moduleSpecifiers } from './import-specifiers.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

function walk(dir) {
  if (!statSync(dir, { throwIfNoEntry: false })?.isDirectory()) return [];
  const files = [];
  const pending = [dir];
  while (pending.length)
    for (const entry of readdirSync(pending.pop(), { withFileTypes: true })) {
      const full = path.join(entry.parentPath, entry.name);
      if (entry.isDirectory()) pending.push(full);
      else if (/\.(ts|mjs|css|py)$/.test(full)) files.push(full);
    }
  return files;
}

const failures = [];
for (const absolute of [
  ...walk(path.join(root, 'explorer/src')),
  ...walk(path.join(root, 'explorer/styles')),
  ...walk(path.join(root, 'explorer/test')),
  ...walk(path.join(root, 'tools/explorer')),
]) {
  const file = path.relative(root, absolute);
  if (file === 'explorer/styles/tokens.css') continue;
  const python = file.endsWith('.py');
  const source = readFileSync(absolute, 'utf8');
  if (/^explorer\/(src|test)\//.test(file) && file.endsWith('.ts')) {
    const packageRoot = path.join(root, 'explorer');
    const area = path.relative(packageRoot, absolute).split(path.sep)[0];
    for (const { value } of moduleSpecifiers(absolute, source)) {
      if (!value.startsWith('.') && !value.startsWith('@/')) continue;
      const target = value.startsWith('@/') ? path.resolve(packageRoot, value.slice(2)) : path.resolve(path.dirname(absolute), value);
      const targetArea = path.relative(packageRoot, target).split(path.sep)[0];
      if (targetArea === '..' || (!value.startsWith('@/') && targetArea !== area))
        failures.push(`${file}: package import boundary: ${value}`);
    }
  }
  source.split('\n').forEach((line, index) => {
    const trimmed = line.trim();
    if (
      trimmed.startsWith('//') ||
      trimmed.startsWith('/*') ||
      trimmed.startsWith('*') ||
      trimmed.startsWith('<!--') ||
      (python && trimmed.startsWith('#'))
    )
      failures.push(`${file}:${index + 1} comment: ${trimmed.slice(0, 70)}`);
  });
}

for (const failure of failures) console.error(failure);
console.log(
  failures.length ? `explorer source: ${failures.length} failure(s)` : 'explorer source: no comments; package import boundaries hold',
);
process.exitCode = failures.length ? 1 : 0;
