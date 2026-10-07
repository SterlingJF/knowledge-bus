#!/usr/bin/env node

// Fills each `<!-- BEGIN AUTO-GENERATED <path>#<heading-slug> -->` region with that section of <path>.
// Marker form after datamodel-code-generator's AUTO-GENERATED regions:
// https://github.com/datamodel-code-generator/datamodel-code-generator/blob/76b83fac38d150410c3bbb850f6595cbb75b3e71/README.md

import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { parseArgs } from 'node:util';

const usage = 'Usage: sync-regions <file.md>... [--check]';
const marker = /<!-- (BEGIN|END) AUTO-GENERATED (\S+?\.md)#([a-z0-9-]+) -->/g;

const { files, check } = readArgs();
let stale = false;

for (const file of files) {
  const original = readFileSync(file, 'utf8');
  const updated = fillRegions(file, original);
  if (updated === original) {
    console.log(`current: ${file}`);
  } else if (check) {
    stale = true;
  } else {
    writeFileSync(file, updated);
    console.log(`wrote: ${file}`);
  }
}
if (stale) process.exitCode = 1;

function readArgs() {
  try {
    const { positionals, values } = parseArgs({
      allowPositionals: true,
      options: { check: { type: 'boolean', default: false } },
    });
    if (positionals.length === 0) fail(usage);
    return { files: positionals, check: values.check };
  } catch {
    return fail(usage);
  }
}

function fillRegions(file, text) {
  const markers = [...text.matchAll(marker)];
  if (markers.length === 0) fail(`${file}: no regions`);
  let output = '';
  let cursor = 0;
  for (let index = 0; index < markers.length; index += 2) {
    const begin = markers[index];
    const end = markers[index + 1];
    const ref = `${begin[2]}#${begin[3]}`;
    if (begin[1] !== 'BEGIN' || end === undefined || end[1] !== 'END' || `${end[2]}#${end[3]}` !== ref) {
      fail(`${file}: unmatched marker for ${ref}`);
    }
    const body = section(resolve(dirname(file), begin[2]), begin[3], ref);
    const region = `${begin[0]}\n\n${body}\n\n${end[0]}`;
    const current = text.slice(begin.index, end.index + end[0].length);
    if (current !== region && check) console.error(`stale: ${file} ${ref}`);
    output += text.slice(cursor, begin.index) + region;
    cursor = end.index + end[0].length;
  }
  return output + text.slice(cursor);
}

function section(path, slug, ref) {
  if (!existsSync(path)) fail(`${ref}: ${path} not found`);
  const lines = readFileSync(path, 'utf8').split('\n');
  let fence = null;
  let level = 0;
  let start = -1;
  for (const [index, line] of lines.entries()) {
    const fenceMatch = /^(`{3,}|~{3,})/.exec(line);
    if (fenceMatch) {
      const char = fenceMatch[1][0];
      if (fence === null) fence = char;
      else if (char === fence) fence = null;
      continue;
    }
    if (fence !== null) continue;
    const heading = /^(#{1,6}) (.+?)\s*$/.exec(line);
    if (!heading) continue;
    if (start === -1 && slugify(heading[2]) === slug) {
      level = heading[1].length;
      start = index + 1;
    } else if (start !== -1 && heading[1].length <= level) {
      return lines.slice(start, index).join('\n').trim();
    }
  }
  if (start === -1) fail(`${ref}: #${slug} not found`);
  return lines.slice(start).join('\n').trim();
}

function slugify(heading) {
  return heading
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .trim()
    .replace(/\s/g, '-');
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
