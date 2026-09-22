import { spawnSync } from 'node:child_process';
import { copyFileSync, cpSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { relativeAliasSpecifiers } from './import-specifiers.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const explorerSrc = path.join(root, 'explorer/src');
const failures: string[] = [];
const sources = new Map(
  walk(explorerSrc).map((file) => [file, relativeAliasSpecifiers(file, readFileSync(file, 'utf8'), path.dirname(explorerSrc))]),
);
const projection = mkdtempSync(path.join(tmpdir(), 'knowledge-bus-explorer-layers-'));
let report: ReturnType<typeof spawnSync>;

try {
  const packageRoot = path.join(projection, 'explorer');
  cpSync(explorerSrc, path.join(packageRoot, 'src'), { recursive: true });
  copyFileSync(path.join(root, 'explorer/package.json'), path.join(packageRoot, 'package.json'));
  for (const [file, source] of sources) writeFileSync(path.join(packageRoot, 'src', path.relative(explorerSrc, file)), source);
  const config = JSON.parse(readFileSync(path.join(root, 'tools/ce-pattern/ce-pattern.json'), 'utf8'));
  config.library.dir = packageRoot;
  const configPath = path.join(projection, 'ce-pattern.json');
  writeFileSync(configPath, JSON.stringify(config));
  report = spawnSync(
    path.join(root, 'node_modules/.bin/tsx'),
    [path.join(root, 'tools/ce-pattern/check-component-layers.ts'), '--config', configPath],
    { encoding: 'utf8', cwd: root },
  );
  report.stdout = String(report.stdout ?? '').replaceAll(packageRoot, path.join(root, 'explorer'));
  report.stderr = String(report.stderr ?? '').replaceAll(packageRoot, path.join(root, 'explorer'));
} finally {
  rmSync(projection, { recursive: true, force: true });
}
process.stdout.write(report.stdout!);
if (report.status !== 0) failures.push('CE layer check refused: ' + (report.stderr || 'see report above').trim());

const advisories = new Set([...String(report.stdout).matchAll(/^advisory\s+(\S+):/gm)].map((m) => m[1]));
const acknowledged = (JSON.parse(readFileSync(path.join(root, 'tools/explorer/component-advisories.json'), 'utf8')).acknowledged ?? []) as {
  file: string;
  note: string;
}[];
const reviewed = new Set(acknowledged.filter((entry) => entry.note.trim().length > 0).map((entry) => entry.file));
for (const file of advisories) if (!reviewed.has(file)) failures.push(`unreviewed CE advisory: ${file}`);
for (const entry of acknowledged) if (!advisories.has(entry.file)) failures.push(`stale advisory acknowledgement: ${entry.file}`);

function walk(dir: string): string[] {
  const files: string[] = [];
  const pending = [dir];
  while (pending.length)
    for (const entry of readdirSync(pending.pop()!, { withFileTypes: true })) {
      const full = path.join(entry.parentPath, entry.name);
      if (entry.isDirectory()) pending.push(full);
      else if (full.endsWith('.ts')) files.push(full);
    }
  return files;
}

for (const file of walk(path.join(explorerSrc, 'lib'))) {
  const source = sources.get(file)!;
  const relative = path.relative(root, file);
  if (/\b(?:document|window)\b|createElement|HTMLElement|addEventListener/.test(source))
    failures.push(`${relative}: lib must stay free of DOM work`);
  if (/from '\.\.\/component-(?:elements|patterns|core)/.test(source)) failures.push(`${relative}: lib must not import component layers`);
}
for (const file of walk(path.join(explorerSrc, 'component-elements')))
  if (/from '\.\.\/component-patterns/.test(sources.get(file)!))
    failures.push(`${path.relative(root, file)}: elements must not import patterns`);
for (const file of walk(explorerSrc)) {
  const source = sources.get(file)!;
  const relative = path.relative(root, file);
  if (/from '(?:\.\.\/)*(?:index|standalone)'/.test(source)) failures.push(`${relative}: components must not import package entries`);
  if (!file.endsWith('standalone.ts') && /document\.getElementById\(/.test(source))
    failures.push(`${relative}: only the standalone entry may look up page elements`);
}

for (const failure of failures) console.error(failure);
console.log(failures.length ? `explorer layers: ${failures.length} failure(s)` : 'explorer layers: CE contract holds');
process.exitCode = failures.length ? 1 : 0;
