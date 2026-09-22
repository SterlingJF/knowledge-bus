import { build } from 'esbuild';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { root } from './generate-tokens.mjs';
import { moduleSpecifiers, relativeAliasSpecifiers } from './import-specifiers.mjs';

export const explorerDir = path.join(root, 'explorer');
export const distDir = path.join(explorerDir, 'dist');
export const standaloneBundle = path.join(distDir, 'standalone.js');
export const installedBundle = path.join(root, 'explorer/prebuilt/viewer.js');
export const installedBundleManifest = path.join(root, 'explorer/prebuilt/viewer.json');

const EXTERNAL_IMPORT = /^\s*(?:import|export)\b[^\n]*\bfrom\s+["'][^.]/m;
const DYNAMIC_LOAD = /\brequire\(|\bimport\(|\bfetch\(|XMLHttpRequest|WebSocket/;

export const shared = {
  bundle: true,
  target: 'es2022',
  loader: { '.css': 'text' },
  charset: 'utf8',
  legalComments: 'none',
  sourcemap: false,
  logLevel: 'silent',
  absWorkingDir: explorerDir,
  tsconfig: path.join(explorerDir, 'tsconfig.json'),
};

export async function buildStandaloneSource() {
  const result = await build({ ...shared, entryPoints: ['src/standalone.ts'], format: 'iife', write: false });
  const source = result.outputFiles[0].text;
  if (EXTERNAL_IMPORT.test(source) || DYNAMIC_LOAD.test(source)) throw new Error('standalone.js reaches outside the bundle.');
  return source;
}

export async function buildExplorer() {
  rmSync(distDir, { recursive: true, force: true });
  mkdirSync(distDir, { recursive: true });
  await build({ ...shared, entryPoints: ['src/index.ts'], format: 'esm', outfile: path.join(distDir, 'index.js') });
  const standalone = await buildStandaloneSource();
  writeFileSync(standaloneBundle, standalone);
  for (const file of ['index.js', 'standalone.js']) {
    const source = readFileSync(path.join(distDir, file), 'utf8');
    if (EXTERNAL_IMPORT.test(source) || DYNAMIC_LOAD.test(source)) throw new Error(`${file} reaches outside the bundle.`);
  }
  const explorerPackage = JSON.parse(readFileSync(path.join(explorerDir, 'package.json'), 'utf8'));
  writeFileSync(installedBundle, standalone);
  writeFileSync(
    installedBundleManifest,
    JSON.stringify(
      {
        id: explorerPackage.name,
        version: explorerPackage.version,
        digest: `sha256:${createHash('sha256').update(standalone).digest('hex')}`,
        bytes: Buffer.byteLength(standalone),
      },
      null,
      2,
    ) + '\n',
  );
  const types = spawnSync(path.join(root, 'node_modules/.bin/tsc'), ['-p', path.join(explorerDir, 'tsconfig.build.json')], {
    stdio: 'inherit',
  });
  if (types.status !== 0) throw new Error('Declaration build failed.');
  const typesRoot = path.join(distDir, 'types');
  const copiedJson = new Set();
  const pending = [typesRoot];
  while (pending.length) {
    const directory = pending.pop();
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const file = path.join(directory, entry.name);
      if (entry.isDirectory()) pending.push(file);
      else if (entry.name.endsWith('.d.ts')) {
        const source = readFileSync(file, 'utf8');
        const normalized = relativeAliasSpecifiers(file, source, typesRoot);
        for (const { value } of moduleSpecifiers(file, source)) {
          if (!value.startsWith('@/') || !value.endsWith('.json') || copiedJson.has(value)) continue;
          const target = path.join(typesRoot, value.slice(2));
          mkdirSync(path.dirname(target), { recursive: true });
          copyFileSync(path.join(explorerDir, value.slice(2)), target);
          copiedJson.add(value);
        }
        writeFileSync(file, normalized);
      }
    }
  }
  writeFileSync(path.join(distDir, 'index.d.ts'), "export * from './types/src/index';\n");
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href)
  buildExplorer().then(
    () => console.log('explorer: built dist/index.js, dist/standalone.js and declarations'),
    (error) => {
      console.error(error.message);
      process.exitCode = 1;
    },
  );
