import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import {
  auditCSS,
  auditLadders,
  auditPartReach,
  auditRoleReach,
  auditRoles,
  auditTokenOwnership,
  auditRuntime,
  auditThemeNumbers,
  auditValueNames,
  auditZoomGrowth,
  validateAuthority,
  validateExceptions,
  findingKey,
} from './token-contract.mjs';
import { root, generatedPath, tokenCss, readAuthority, flattenAuthority, closedSelectors } from './generate-tokens.mjs';
import { patternsPath, placements, selectorsByToken } from './tokens-report.mjs';

const exceptionsPath = path.join(root, 'tools/explorer/visual-geometry-exceptions.json');

function walk(dir, test) {
  if (!statSync(dir, { throwIfNoEntry: false })?.isDirectory()) return [];
  return readdirSync(dir).flatMap((entry) => {
    const full = path.join(dir, entry);
    return statSync(full).isDirectory() ? walk(full, test) : test(full) ? [full] : [];
  });
}

export function sourceFiles() {
  return [
    ...walk(path.join(root, 'explorer/src'), (f) => f.endsWith('.ts') && !f.endsWith('.d.ts')),
    ...walk(path.join(root, 'explorer/styles'), (f) => f.endsWith('.css') && f !== generatedPath),
  ].sort();
}

export function inventory(files = sourceFiles()) {
  const manifest = readAuthority();
  const tokens = flattenAuthority(manifest);
  const owners = closedSelectors(manifest);
  const findings = [];
  const consumers = [];
  const strays = [];
  const themeReads = [];
  for (const absolute of files) {
    const file = path.relative(root, absolute);
    const source = readFileSync(absolute, 'utf8');
    for (const match of source.matchAll(/(?:var\(|['"])(--kb-[\w-]+)/g))
      consumers.push({ file, line: source.slice(0, match.index).split('\n').length, token: match[1] });
    if (absolute.endsWith('.css')) {
      for (const finding of auditCSS(source, tokens)) findings.push({ ...finding, file });
      for (const stray of auditTokenOwnership(source, owners))
        strays.push(`${file}:${stray.line} ${stray.selector} belongs to ${stray.part} but references ${stray.token}`);
    } else {
      for (const finding of auditRuntime(source, tokens)) findings.push({ ...finding, file });
      for (const read of auditThemeNumbers(source, tokens))
        themeReads.push(`${file}:${read.line} tokenNumber(${read.token}) reads a token whose value changes with the theme`);
    }
  }
  return {
    manifest,
    tokens,
    findings: [...new Map(findings.map((f) => [findingKey(f), f])).values()],
    consumers,
    strays,
    themeReads,
  };
}

export function checkTokens() {
  const { manifest, tokens, findings, consumers, strays, themeReads } = inventory();
  const errors = validateAuthority(tokens);
  for (const consumer of consumers) if (!tokens[consumer.token]) errors.push(`${consumer.file}:${consumer.line} missing ${consumer.token}`);
  if (readFileSync(generatedPath, 'utf8') !== tokenCss(manifest)) errors.push('Generated token CSS is stale; run generate:explorer:tokens');
  const declared = new Set(consumers.map((c) => c.token));
  for (const name of Object.keys(tokens))
    if (!declared.has(name) && !Object.values(tokens).some((t) => t.value.includes(`var(${name})`)))
      errors.push(`authority: ${name} is never consumed`);
  errors.push(...strays);
  errors.push(...themeReads);
  errors.push(...auditRoles(tokens));
  errors.push(...auditLadders(manifest.roles));
  errors.push(...auditValueNames(tokens));
  errors.push(...auditZoomGrowth(tokens));
  const drawnBy = Object.fromEntries(
    [...selectorsByToken(readFileSync(patternsPath, 'utf8'), Object.keys(tokens))].map(([name, found]) => [name, [...found]]),
  );
  errors.push(...auditPartReach(manifest.parts, drawnBy));
  const placed = placements(manifest);
  const roleTokens = Object.fromEntries(Object.entries(tokens).filter(([name]) => placed.get(name).tier === 'role'));
  errors.push(...auditRoleReach(manifest.parts, roleTokens, drawnBy));
  errors.push(...validateExceptions(findings, JSON.parse(readFileSync(exceptionsPath, 'utf8'))));
  return { errors, tokens, findings, consumers };
}
