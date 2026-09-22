import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { root } from './generate-tokens.mjs';

const ALLOWED_URL = /^(?:https?:)?\/\/www\.w3\.org\//;
const MACHINE_PATH = /\/Users\/|\/home\/|[A-Z]:\\\\/;
const DRAWABLE_PATH_DATA = /^[Mm][0-9eE,.\-+ \t]*[0-9][MmZzLlHhVvCcSsQqTtAa0-9,.\-+eE \t]*$/;
const A_MONOGRAM_FITS_THE_ICON_BOX = /^[\p{L}\p{N}]{1,2}$/u;
const NON_FINITE_GEOMETRY =
  /\s(?:d|transform|points|viewBox|x|y|x1|y1|x2|y2|cx|cy|r|rx|ry|width|height|stroke-width|stroke-dasharray|font-size|opacity|offset)="[^"]*\b(?:NaN|Infinity)\b/;

export function checkHtml(name, html) {
  const failures = [];
  const push = (message) => failures.push(`${name}: ${message}`);
  if (!html.includes('id="explorer-model"')) push('missing embedded model');
  if (!/<script>[\s\S]+<\/script>/.test(html)) push('missing inline viewer script');
  if (/<script[^>]*\ssrc=|<link[^>]*\shref=|@import\b/.test(html)) push('references an external resource');
  for (const [url] of html.matchAll(/https?:\/\/[^\s"'<)]+/g)) if (!ALLOWED_URL.test(url)) push(`external URL ${url}`);
  if (MACHINE_PATH.test(html)) push('contains a machine path');
  if (/\bfetch\(|\bimport\(|XMLHttpRequest|WebSocket/.test(html)) push('viewer script requests remote content');
  if (/window\.openai|lucide|\/opt\/homebrew|visualize\.html|unpkg\.com/.test(html)) push('prototype host dependency leaked');
  if (!html.includes('<noscript>')) push('missing JavaScript-disabled notice');
  const model = html.match(/<script type="application\/json" id="explorer-model">([\s\S]*?)<\/script>/);
  if (!model) push('embedded model is not a JSON script block');
  else {
    if (/[<>&]/.test(model[1])) push('embedded model contains unescaped markup characters');
    try {
      const parsed = JSON.parse(model[1]);
      if (parsed.schema !== 'knowledge-bus/explorer-model/1') push('embedded model is not an Explorer model');
      if (!Array.isArray(parsed.wiring)) push('embedded model carries no frame wiring');
      for (const [subject, mark] of Object.entries(parsed.marks?.declared ?? {})) {
        const drawnInline =
          mark && typeof mark === 'object' && Object.keys(mark).length === 1
            ? typeof mark.monogram === 'string'
              ? A_MONOGRAM_FITS_THE_ICON_BOX.test(mark.monogram)
              : typeof mark.glyph === 'string' && DRAWABLE_PATH_DATA.test(mark.glyph)
            : false;
        if (!drawnInline) push(`declared mark for ${subject} is referenced rather than drawn inline`);
      }
    } catch {
      push('embedded model is not valid JSON');
    }
  }
  return failures;
}

export function checkSvg(name, svg) {
  const failures = [];
  const push = (message) => failures.push(`${name}: ${message}`);
  if (!svg.startsWith('<svg xmlns="http://www.w3.org/2000/svg"')) push('missing svg root with xmlns');
  for (const attribute of ['width', 'height', 'viewBox'])
    if (!new RegExp(`<svg[^>]*\\s${attribute}="[^"]+"`).test(svg)) push(`missing ${attribute}`);
  if (!/<title>[^<]+<\/title>/.test(svg)) push('missing title');
  if (!/<desc>[^<]+<\/desc>/.test(svg)) push('missing desc');
  if (/<script|foreignObject|\son[a-z]+\s*=\s*["']|<image|<use\b|xlink:href|@import|url\(/i.test(svg))
    push('contains scripts, embeds, or external references');
  for (const [url] of svg.matchAll(/https?:\/\/[^\s"'<)]+/g)) if (!ALLOWED_URL.test(url)) push(`external URL ${url}`);
  if (!svg.includes('prefers-color-scheme')) push('not a dual-theme file');
  if (/light-dark\(/.test(svg)) push('leaves light-dark() unresolved');
  const declared = new Set([...svg.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
  for (const [, token] of svg.matchAll(/var\((--[\w-]+)/g)) if (!declared.has(token)) push(`unresolved variable ${token}`);
  if (!/<g data-entity=/.test(svg)) push('exports no cards');
  if (!/<text /.test(svg)) push('exports no text');
  if (MACHINE_PATH.test(svg)) push('contains a machine path');
  if (NON_FINITE_GEOMETRY.test(svg)) push('exports a geometry value that is not a finite number');
  const base = svg.match(/<style>svg\{([^}]+)\}/);
  const light = svg.match(/@media\(prefers-color-scheme:light\)\{svg\{([^}]+)\}\}/);
  if (!base || !light) push('missing one of the two theme variable sets');
  else if (base[1] === light[1]) push('both theme variable sets are identical');
  return failures;
}

export function checkDirectory(dir) {
  if (!existsSync(dir)) return [`${path.relative(root, dir)}: no generated artifacts; run render:explorer first`];
  const files = readdirSync(dir);
  const html = files.filter((f) => f.endsWith('.html'));
  const svg = files.filter((f) => f.endsWith('.svg'));
  const failures = [];
  if (!html.length || !svg.length) failures.push(`${path.relative(root, dir)}: expected at least one HTML and one SVG artifact`);
  for (const file of html) failures.push(...checkHtml(file, readFileSync(path.join(dir, file), 'utf8')));
  for (const file of svg) failures.push(...checkSvg(file, readFileSync(path.join(dir, file), 'utf8')));
  return failures;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const failures = checkDirectory(path.resolve(root, process.argv[2] ?? 'dist/explorer'));
  for (const failure of failures) console.error(failure);
  console.log(failures.length ? `explorer artifacts: ${failures.length} failure(s)` : 'explorer artifacts: self-contained and complete');
  process.exitCode = failures.length ? 1 : 0;
}
