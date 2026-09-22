import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { root, authorityPath, readAuthority, flattenAuthority, PALETTE, tokenLeaves } from './generate-tokens.mjs';

export const patternsPath = path.join(root, 'explorer/styles/patterns.css');

const SKIPPED_DIRECTORIES = new Set(['node_modules', '.git', '.venv', 'dist', '.pytest_cache', '.ruff_cache', '__pycache__']);
const SCANNED_EXTENSIONS = new Set(['.ts', '.tsx', '.mjs', '.js', '.css', '.json', '.md', '.yaml', '.yml', '.py', '.html', '.svg']);
const ALIAS_HOPS = 20;
const NUMERIC = /^-?(?:\d+\.?\d*|\.\d+)(?:px|%|ms|s)?$/;
const LIGHT_DARK = /^light-dark\(([^,]+),([^)]+)\)$/;
const COLUMN_GAP = '  ';
const EMPTY_CELL = '-';

export const referencePattern = (name) => new RegExp('(?<![\\w-])' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?![\\w-])');

export function placements(manifest) {
  const placed = new Map();
  for (const [group, entries] of Object.entries(manifest.roles ?? {}))
    for (const leaf of tokenLeaves(entries))
      placed.set(group === PALETTE ? `--kb-${leaf}` : `--kb-${group}-${leaf}`, { tier: 'role', group });
  for (const [part, entries] of Object.entries(manifest.parts ?? {}))
    for (const leaf of tokenLeaves(entries)) placed.set(`--kb-${part}-${leaf}`, { tier: 'part', group: part });
  return placed;
}

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) return SKIPPED_DIRECTORIES.has(entry.name) ? [] : walk(full);
    return SCANNED_EXTENSIONS.has(path.extname(entry.name)) ? [full] : [];
  });
}

export function scannedFiles(from = root) {
  return statSync(from, { throwIfNoEntry: false })?.isDirectory() ? walk(from).sort() : [];
}

export function themeValue(raw, theme) {
  const pair = raw.match(LIGHT_DARK);
  return pair ? pair[theme === 'light' ? 1 : 2].trim() : raw;
}

export function resolveTheme(tokens, theme) {
  const sided = {};
  for (const [name, token] of Object.entries(tokens)) sided[name] = themeValue(token.value, theme);
  const flatten = (value, depth = 0) =>
    depth > ALIAS_HOPS
      ? value
      : value.replace(/var\((--[\w-]+)(?:\s*,[^)]*)?\)/g, (whole, name) =>
          sided[name] === undefined ? whole : flatten(sided[name], depth + 1),
        );
  const resolved = {};
  for (const name of Object.keys(sided)) resolved[name] = flatten(sided[name]);
  return resolved;
}

export function cssRules(css) {
  const rules = [];
  const stack = [];
  let pending = '';
  let body = '';
  for (const character of css.replace(/\/\*[\s\S]*?\*\//g, '')) {
    if (character === '{') {
      stack.push({ prelude: pending.trim(), body });
      pending = '';
      body = '';
    } else if (character === '}') {
      const frame = stack.pop() ?? { prelude: '', body: '' };
      if (frame.prelude && !frame.prelude.startsWith('@')) rules.push({ prelude: frame.prelude, body: body + pending });
      body = frame.body;
      pending = '';
    } else if (character === ';') {
      body += pending + ';';
      pending = '';
    } else pending += character;
  }
  return rules;
}

export function splitSelectors(prelude) {
  const selectors = [];
  let depth = 0;
  let current = '';
  for (const character of prelude) {
    if (character === '(' || character === '[') depth += 1;
    else if (character === ')' || character === ']') depth -= 1;
    if (character === ',' && depth === 0) {
      selectors.push(current);
      current = '';
    } else current += character;
  }
  selectors.push(current);
  return selectors.map((selector) => selector.trim().replace(/\s+/g, ' ')).filter(Boolean);
}

export function selectorsByToken(css, names) {
  const index = new Map(names.map((name) => [name, new Set()]));
  for (const rule of cssRules(css))
    for (const name of names)
      if (referencePattern(name).test(rule.body)) for (const selector of splitSelectors(rule.prelude)) index.get(name).add(selector);
  return index;
}

export function filesByToken(files, names) {
  const index = new Map(names.map((name) => [name, []]));
  for (const absolute of files) {
    const source = readFileSync(absolute, 'utf8');
    if (!source.includes('--kb-')) continue;
    const relative = path.relative(root, absolute);
    for (const name of names) if (referencePattern(name).test(source)) index.get(name).push(relative);
  }
  return index;
}

const sortKey = (value) => (NUMERIC.test(value.trim()) ? parseFloat(value) : null);

export function tokenReport() {
  const manifest = readAuthority();
  const tokens = flattenAuthority(manifest);
  const placed = placements(manifest);
  const names = Object.keys(tokens);
  const light = resolveTheme(tokens, 'light');
  const dark = resolveTheme(tokens, 'dark');
  const selectors = selectorsByToken(readFileSync(patternsPath, 'utf8'), names);
  const files = filesByToken(scannedFiles(), names);
  const rows = names.map((name) => ({
    name,
    tier: placed.get(name).tier,
    group: placed.get(name).group,
    kind: tokens[name].kind,
    role: tokens[name].role,
    raw: tokens[name].value,
    light: light[name],
    dark: dark[name],
    files: files.get(name),
    selectors: [...selectors.get(name)].sort(),
    selectorCount: selectors.get(name).size,
  }));
  rows.sort((a, b) => {
    if (a.tier !== b.tier) return a.tier.localeCompare(b.tier);
    if (a.group !== b.group) return a.group.localeCompare(b.group);
    const left = sortKey(a.light);
    const right = sortKey(b.light);
    if ((left === null) !== (right === null)) return left === null ? 1 : -1;
    if (left !== null && left !== right) return left - right;
    if (a.light !== b.light) return a.light.localeCompare(b.light);
    return a.name.localeCompare(b.name);
  });
  return { authority: path.relative(root, authorityPath), stylesheet: path.relative(root, patternsPath), tokens: rows };
}

function alignedTable(headers, cells) {
  const widths = headers.map((header, column) => Math.max(header.length, ...cells.map((row) => row[column].length)));
  const line = (row) =>
    row
      .map((cell, column) => cell.padEnd(widths[column]))
      .join(COLUMN_GAP)
      .trimEnd();
  return [line(headers), line(widths.map((width) => '-'.repeat(width))), ...cells.map(line)];
}

export function formatReport(report) {
  const headers = ['TOKEN', 'TIER', 'GROUP', 'KIND', 'RAW', 'LIGHT', 'DARK', 'SEL', 'FILES', 'ROLE'];
  const cells = report.tokens.map((token) => [
    token.name,
    token.tier,
    token.group,
    token.kind,
    token.raw,
    token.light,
    token.dark,
    String(token.selectorCount),
    String(token.files.length),
    token.role,
  ]);
  const references = report.tokens.flatMap((token) => [
    token.name,
    `  files      ${token.files.join(', ') || EMPTY_CELL}`,
    `  selectors  ${token.selectors.join(', ') || EMPTY_CELL}`,
  ]);
  return [
    `authority  ${report.authority}`,
    `stylesheet ${report.stylesheet}`,
    `tokens     ${report.tokens.length}`,
    '',
    ...alignedTable(headers, cells),
    '',
    'REFERENCES',
    ...references,
  ].join('\n');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const { values } = parseArgs({ options: { json: { type: 'boolean', default: false } } });
  const report = tokenReport();
  console.log(values.json ? JSON.stringify(report, null, 2) : formatReport(report));
}
