import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { buildStandaloneSource, installedBundle, installedBundleManifest } from './build.mjs';

const expected = await buildStandaloneSource();
const actual = readFileSync(installedBundle, 'utf8');
const manifest = JSON.parse(readFileSync(installedBundleManifest, 'utf8'));
const digest = `sha256:${createHash('sha256').update(actual).digest('hex')}`;
if (actual !== expected) throw new Error('Installed Explorer viewer bundle is stale; run build:explorer.');
if (manifest.digest !== digest || manifest.bytes !== Buffer.byteLength(actual))
  throw new Error('Installed Explorer viewer manifest does not match its bundle.');
console.log('explorer viewer: installed bundle is fresh');
