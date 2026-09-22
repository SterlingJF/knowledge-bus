import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const authorityPath = path.join(root, 'explorer/styles/visual-tokens.json');
export const generatedPath = path.join(root, 'explorer/styles/tokens.css');

export const SELECTORS = 'selectors';
export const CLOSED = 'closed';
export const BASE = 'base';
export const FINE_WORK = 'fineWork';
export const PALETTE = 'color';

const declaresToken = (leaf) => leaf !== null && typeof leaf === 'object' && !Array.isArray(leaf);

export const tokenLeaves = (entries) => Object.keys(entries).filter((leaf) => declaresToken(entries[leaf]));

export function flattenAuthority(manifest) {
  const tokens = {};
  const claim = (name, token) => {
    if (tokens[name]) throw new Error('Two authority entries flatten to ' + name);
    tokens[name] = token;
  };
  for (const [group, entries] of Object.entries(manifest.roles ?? {}))
    for (const leaf of tokenLeaves(entries)) claim(group === PALETTE ? `--kb-${leaf}` : `--kb-${group}-${leaf}`, entries[leaf]);
  for (const [part, entries] of Object.entries(manifest.parts ?? {}))
    for (const leaf of tokenLeaves(entries)) claim(`--kb-${part}-${leaf}`, entries[leaf]);
  return tokens;
}

export function closedSelectors(manifest) {
  const closed = {};
  for (const [part, entries] of Object.entries(manifest.parts ?? {}))
    if (entries[CLOSED] && entries[SELECTORS]) closed[part] = entries[SELECTORS];
  return closed;
}

export const readAuthority = () => JSON.parse(readFileSync(authorityPath, 'utf8'));

export function tokenCss(manifest) {
  return (
    '/* Generated from visual-tokens.json. Do not edit. */\n' +
    manifest.scope +
    '{\n' +
    Object.entries(flattenAuthority(manifest))
      .map(([name, token]) => '  ' + name + ': ' + token.value + ';')
      .join('\n') +
    '\n}\n'
  );
}

export function themeValues(manifest, theme) {
  const index = theme === 'light' ? 1 : 2;
  const resolved = {};
  for (const [name, token] of Object.entries(flattenAuthority(manifest))) {
    const pair = token.value.match(/^light-dark\(([^,]+),([^)]+)\)$/);
    resolved[name] = pair ? pair[index].trim() : token.value;
  }
  return resolved;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  writeFileSync(generatedPath, tokenCss(readAuthority()));
  console.log('explorer tokens: wrote explorer/styles/tokens.css');
}
