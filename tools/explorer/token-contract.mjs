import { BASE, FINE_WORK, SELECTORS, tokenLeaves } from './generate-tokens.mjs';

const refs = (s) => [...s.matchAll(/var\(\s*(--[\w-]+)/g)].map((m) => m[1]);
const lineAt = (s, i) => s.slice(0, i).split('\n').length;

export const KINDS = ['color', 'paint', 'length', 'font', 'duration', 'transition', 'number', 'filter', 'shadow'];
const ALIAS_HOPS = 20;
const ALIAS_REFERENCE = /var\(\s*(--[\w-]+)\s*(?:,[^)]*)?\)/g;
const HEX_LITERAL = /#[0-9a-f]{3,8}\b/gi;
const PAINT_WORD = /\b(?:transparent|currentColor)\b/gi;
const COLOR_CALL = /(?:color-mix|rgba?|hsla?|hwb|oklab|oklch|lab|lch|color)\(/i;
const IMAGE_CALL = /(?:(?:repeating-)?(?:linear|radial|conic)-gradient|image-set|url|cross-fade)\(/i;
const FILTER_CALL = /(?<![\w-])(?:blur|brightness|contrast|drop-shadow|grayscale|hue-rotate|invert|opacity|saturate|sepia)\(/i;
const COLOR_HEAD = new RegExp('^(?:#[0-9a-f]{3,8}\\b|transparent\\b|currentcolor\\b|' + COLOR_CALL.source + ')', 'i');
const PAINT_HEAD = new RegExp(COLOR_HEAD.source + '|^(?:' + IMAGE_CALL.source + ')', 'i');
const PAINT_CALL_HEAD = new RegExp('(?<![\\w-])(?:' + COLOR_CALL.source + '|' + IMAGE_CALL.source + '|light-dark\\()', 'i');
const NUMBER_WITH_UNIT = /(?<![\w.#-])(-?(?:\d+(?:\.\d+)?|\.\d+))([a-z%]*)/gi;
const LENGTH_UNIT = /^(?:px|rem|em|ch|ex|vh|vw|vmin|vmax|dvh|dvw|svh|svw|lvh|lvw|cqw|cqh|cqi|cqb|cqmin|cqmax|pt|pc|in|cm|mm|q|%)$/i;
const TIME_UNIT = /^m?s$/i;
const LIGHT_DARK_HEAD = /^light-dark\(/i;
const INSET_KEYWORD = /(?<![\w-])inset(?![\w-])/gi;
const SHADOW_OFFSETS = { least: 2, most: 4 };
const TRANSITION_TIMES = { least: 1, most: 2 };

function closingParen(value, opening) {
  let depth = 0;
  for (let cursor = opening; cursor < value.length; cursor += 1) {
    if (value[cursor] === '(') depth += 1;
    else if (value[cursor] === ')') {
      depth -= 1;
      if (depth === 0) return cursor;
    }
  }
  return -1;
}

function splitTopLevel(text) {
  const parts = [];
  let depth = 0;
  let current = '';
  for (const character of text) {
    if (character === '(') depth += 1;
    else if (character === ')') depth -= 1;
    if (character === ',' && depth === 0) {
      parts.push(current);
      current = '';
    } else current += character;
  }
  parts.push(current);
  return parts.map((part) => part.trim());
}

export function resolveAliases(tokens, value, depth = 0) {
  if (depth > ALIAS_HOPS) return value;
  return value.replace(ALIAS_REFERENCE, (whole, dependency) =>
    tokens[dependency] ? resolveAliases(tokens, tokens[dependency].value, depth + 1) : whole,
  );
}

export function themeBranches(value) {
  const trimmed = value.trim();
  if (!LIGHT_DARK_HEAD.test(trimmed)) return [trimmed];
  const close = closingParen(trimmed, trimmed.indexOf('('));
  if (close !== trimmed.length - 1) return [trimmed];
  const sides = splitTopLevel(trimmed.slice(trimmed.indexOf('(') + 1, close));
  return sides.length === 2 ? sides : [trimmed];
}

function withoutCalls(value, head) {
  let stripped = value;
  for (;;) {
    const match = head.exec(stripped);
    if (!match) return stripped;
    const close = closingParen(stripped, match.index + match[0].length - 1);
    if (close === -1) return stripped;
    stripped = stripped.slice(0, match.index) + ' ' + stripped.slice(close + 1);
  }
}

const withoutPaints = (value) => withoutCalls(value.replace(HEX_LITERAL, ' ').replace(PAINT_WORD, ' '), PAINT_CALL_HEAD);

function quantities(value) {
  return [...value.replace(HEX_LITERAL, ' ').matchAll(NUMBER_WITH_UNIT)].map((match) => ({ text: match[1], unit: match[2] }));
}

function carriesPaint(value) {
  HEX_LITERAL.lastIndex = 0;
  PAINT_WORD.lastIndex = 0;
  return HEX_LITERAL.test(value) || PAINT_WORD.test(value) || COLOR_CALL.test(value) || IMAGE_CALL.test(value);
}

const isLength = (quantity) => LENGTH_UNIT.test(quantity.unit) || (quantity.unit === '' && parseFloat(quantity.text) === 0);
const bareOf = (value) => value.replace(HEX_LITERAL, ' ').replace(NUMBER_WITH_UNIT, ' ');
const wordless = (value) => !/[a-z]/i.test(bareOf(value));

function isFilterList(branch) {
  const stripped = withoutCalls(branch, FILTER_CALL);
  return stripped !== branch && stripped.trim() === '';
}

function isTransition(branch) {
  return splitTopLevel(branch).every((layer) => {
    const times = quantities(layer);
    return (
      times.length >= TRANSITION_TIMES.least &&
      times.length <= TRANSITION_TIMES.most &&
      times.every((time) => TIME_UNIT.test(time.unit)) &&
      !wordless(layer)
    );
  });
}

function branchMatchesKind(kind, branch) {
  if (kind === 'color') return COLOR_HEAD.test(branch);
  if (kind === 'paint') return PAINT_HEAD.test(branch);
  if (kind === 'filter') return isFilterList(branch);
  if (kind === 'shadow') {
    const skeleton = withoutPaints(branch).replace(INSET_KEYWORD, ' ');
    const offsets = quantities(skeleton);
    return offsets.length >= SHADOW_OFFSETS.least && offsets.length <= SHADOW_OFFSETS.most && offsets.every(isLength) && wordless(skeleton);
  }
  if (carriesPaint(branch)) return false;
  if (kind === 'transition') return isTransition(branch);
  const measures = quantities(branch);
  if (kind === 'font') return measures.length === 0 && /[a-z]/i.test(branch);
  if (measures.length === 0) return false;
  if (kind === 'length') return measures.every(isLength);
  if (kind === 'number') return measures.every((measure) => measure.unit === '') && wordless(branch);
  return measures.length === 1 && TIME_UNIT.test(measures[0].unit) && wordless(branch);
}

export function kindMismatch(tokens, name) {
  const token = tokens[name];
  if (!token?.value || !KINDS.includes(token.kind)) return null;
  const resolved = resolveAliases(tokens, token.value);
  const offending = themeBranches(resolved).find((branch) => !branchMatchesKind(token.kind, branch));
  return offending === undefined ? null : `Kind ${token.kind} does not describe ${name}: ${offending}`;
}

export function validateAuthority(tokens) {
  const errors = [];
  for (const [name, t] of Object.entries(tokens)) {
    if (!/^--kb-[a-z0-9-]+$/.test(name) || !KINDS.includes(t.kind) || !t.role?.trim() || !t.value) errors.push('Invalid token ' + name);
    const mismatch = kindMismatch(tokens, name);
    if (mismatch) errors.push(mismatch);
    const visit = (key, path = []) => {
      if (path.includes(key)) {
        errors.push('Alias cycle: ' + [...path, key].join(' → '));
        return;
      }
      for (const dep of refs(tokens[key]?.value || '')) {
        if (!tokens[dep]) errors.push('Unknown alias ' + dep);
        else visit(dep, [...path, key]);
      }
    };
    visit(name);
  }
  return [...new Set(errors)];
}
export function declarations(css) {
  const clean = css.replace(/\/\*[\s\S]*?\*\//g, (m) => ' '.repeat(m.length));
  return [...clean.matchAll(/(?:^|[;{])\s*([\w-]+)\s*:\s*([^;{}]+)(?=[;}])/g)].map((m) => ({
    property: m[1],
    value: m[2].trim(),
    line: lineAt(css, m.index),
    index: m.index,
  }));
}
function unknownRefs(value, tokens) {
  return refs(value).filter((n) => n.startsWith('--kb-') && !tokens[n]);
}
export function blocks(css) {
  const clean = css.replace(/\/\*[\s\S]*?\*\//g, (m) => ' '.repeat(m.length));
  return [...clean.matchAll(/([^{}]+)\{([^{}]*)\}/g)]
    .map((m) => ({ selector: m[1].trim().replace(/\s+/g, ' '), body: m[2], line: lineAt(css, m.index) }))
    .filter((b) => !b.selector.startsWith('@'));
}
export function partReach(parts, drawnBy) {
  const findings = [];
  for (const [part, entries] of Object.entries(parts)) {
    const declared = entries[SELECTORS];
    if (!declared) continue;
    for (const leaf of tokenLeaves(entries)) {
      const token = `--kb-${part}-${leaf}`;
      for (const selector of drawnBy[token] ?? [])
        if (!declared.some((claimed) => selector.includes(claimed))) findings.push({ token, selector, part });
    }
  }
  return findings;
}

export const partsWithoutSelectors = (parts) => Object.keys(parts).filter((part) => !parts[part][SELECTORS]);

export function auditPartReach(parts, drawnBy) {
  return [
    ...partsWithoutSelectors(parts).map((part) => `parts.${part} declares no selectors, so nothing holds its tokens to the rules it draws`),
    ...partReach(parts, drawnBy).map(
      (finding) => `${finding.selector} reaches ${finding.token}, which parts.${finding.part} declares but does not draw there`,
    ),
  ];
}
const ROLE_ENUMERATION = /[,;:—]|\band\b/i;
const rolePartPattern = (part) => new RegExp('(?<![a-z])' + part.split('-').join('[ -]?') + 's?(?![a-z])', 'gi');
const namePartPattern = (part) => new RegExp('(?<![a-z])' + part.split('-').join('-?') + '(?![a-z])', 'i');

export function rolePartClaim(role, parts) {
  const phrase = role.trim();
  if (ROLE_ENUMERATION.test(phrase)) return null;
  const claimed = parts.filter((part) =>
    [...phrase.matchAll(rolePartPattern(part))].some((found) => found.index + found[0].length < phrase.length),
  );
  return claimed.length === 1 ? claimed[0] : null;
}

export function roleReach(parts, tokens, drawnBy) {
  const named = Object.keys(parts);
  const drawers = (selector) => named.filter((part) => (parts[part][SELECTORS] ?? []).some((claimed) => selector.includes(claimed)));
  const findings = [];
  for (const [token, entry] of Object.entries(tokens)) {
    const claim = rolePartClaim(entry.role ?? '', named);
    if (!claim) continue;
    const reached = (drawnBy[token] ?? []).map((selector) => ({ selector, drawn: drawers(selector) }));
    if (reached.some((found) => found.drawn.includes(claim))) continue;
    for (const found of reached)
      for (const part of found.drawn)
        if (part !== claim && !namePartPattern(part).test(token))
          findings.push({ token, selector: found.selector, part, claim, role: entry.role });
  }
  return findings;
}

export function auditRoleReach(parts, tokens, drawnBy) {
  return [
    ...new Set(
      roleReach(parts, tokens, drawnBy).map(
        (finding) => `${finding.selector} reaches ${finding.token}, which parts.${finding.claim} owns by role: ${finding.role}`,
      ),
    ),
  ];
}
export function auditTokenOwnership(css, owners) {
  const parts = Object.entries(owners);
  const findings = [];
  for (const block of blocks(css)) {
    const part = parts.find(([, claimed]) =>
      claimed.some((selector) => block.selector.split(',').some((piece) => piece.trim().includes(selector))),
    );
    if (!part) continue;
    const prefix = `--kb-${part[0]}-`;
    for (const name of new Set(refs(block.body)))
      if (name.startsWith('--kb-') && !name.startsWith(prefix))
        findings.push({ selector: block.selector, token: name, part: part[0], line: block.line });
  }
  return findings;
}
const PAINT_PROPERTY = /^(?:color|background(?:-color)?|border-color|fill|stroke)$/;
const NEUTRAL_KEYWORDS = ['transparent', 'currentColor', 'none', 'inherit', 'initial', 'unset'];
const IDENTITY_FALLBACK = /^[01]$/;
const FALLBACK_LITERAL = /#[0-9a-f]{3,8}\b|\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix)\(|(?:^|[^\w-])(?:\d*\.)?\d+/i;
const BARE_KEYWORD = /^[a-z]+$/i;
const BORDER_WIDTH_PROPERTY = /^border(?:-(?:top|right|bottom|left|block|inline)(?:-(?:start|end))?)?(?:-width)?$/;
const CAMERA_SCALE_REFERENCE = /(?<![\w-])var\(\s*--zoom-scale\b/;
const VAR_OPENING = /(?<![\w-])var\(/;
const SURFACE_PREFIX = /^(?:svg|markup|inline):/;
const QUOTED_STRING = /^(['"`])([\s\S]*)\1$/;
const DECLARATION_LISTS = ['style', 'style-object'];
const DECLARATION_BREAK = /[;,]/;

const namesLiteralColor = (property, value) =>
  PAINT_PROPERTY.test(property) && BARE_KEYWORD.test(value) && !NEUTRAL_KEYWORDS.includes(value);

export const cssPropertyName = (property) =>
  property
    .replace(SURFACE_PREFIX, '')
    .trim()
    .replace(/[A-Z]/g, (letter) => '-' + letter.toLowerCase());

const unquote = (value) => {
  const quoted = value.trim().match(QUOTED_STRING);
  return quoted ? quoted[2].trim() : value.trim();
};

export function runtimeDeclarations(property, value) {
  const name = cssPropertyName(property);
  const body = unquote(value);
  if (!DECLARATION_LISTS.includes(name)) return [{ property: name, value: body }];
  return body
    .replace(/^[\s{]+|[\s}]+$/g, '')
    .split(DECLARATION_BREAK)
    .map((piece) => piece.split(':'))
    .filter((pair) => pair.length > 1)
    .map(([key, ...rest]) => ({ property: cssPropertyName(key), value: unquote(rest.join(':')) }));
}

export function varReferences(value) {
  const found = [];
  for (const match of value.matchAll(new RegExp(VAR_OPENING, 'g'))) {
    const open = match.index + match[0].length - 1;
    const close = closingParen(value, open);
    if (close === -1) continue;
    const [declared, ...fallback] = splitTopLevel(value.slice(open + 1, close));
    found.push({ name: declared, fallback: fallback.length ? fallback.join(',').trim() : null });
  }
  return found;
}

const withoutNestedVars = (value) => withoutCalls(value, VAR_OPENING);

export function fallbackLiterals(value, property) {
  return varReferences(value)
    .filter((reference) => reference.fallback !== null)
    .map((reference) => ({ ...reference, remainder: withoutNestedVars(reference.fallback).trim() }))
    .filter(
      (reference) =>
        !IDENTITY_FALLBACK.test(reference.remainder) &&
        (FALLBACK_LITERAL.test(reference.remainder) ||
          (PAINT_PROPERTY.test(property) && BARE_KEYWORD.test(reference.remainder) && !NEUTRAL_KEYWORDS.includes(reference.remainder))),
    );
}

function hasLiteral(value) {
  const stripped = value
    .replace(/var\([^)]*\)/g, '')
    .replace(/!important/g, '')
    .replace(/\b(?:translate[XY]?|scale|repeat|rgba?|hsl|rotate|matrix)\b/g, '');
  return (
    /#[0-9a-f]{3,8}\b|\b(?:rgba?|hsla?|oklch|lab|color)\(/i.test(stripped) ||
    /(?:^|[^\w-])(?:\d*\.)?\d+(?:px|rem|em|vh|vw|dvh|%|ms|s|deg)?\b/.test(stripped)
  );
}
export function auditCSS(css, tokens) {
  const findings = [];
  for (const d of declarations(css)) {
    if (d.property.startsWith('--kb-')) findings.push({ ...d, reason: 'Canonical redeclaration' });
    else if (unknownRefs(d.value, tokens).length) findings.push({ ...d, reason: 'Unknown token' });
    else if (fallbackLiterals(d.value, d.property).length) findings.push({ ...d, reason: 'Literal in a var fallback' });
    else if (namesLiteralColor(d.property, d.value)) findings.push({ ...d, reason: 'Literal named color' });
    else if (BORDER_WIDTH_PROPERTY.test(d.property) && CAMERA_SCALE_REFERENCE.test(d.value))
      findings.push({ ...d, reason: 'Border width follows the camera' });
    else if (
      hasLiteral(d.value) &&
      !/^\s*0(?:\s*!important)?$/.test(d.value) &&
      !['flex-shrink', 'order', 'z-index', 'grid-column', 'grid-row'].includes(d.property)
    ) {
      const structural = d.value.replace(/var\([^)]*\)/g, '').replace(/100(?:%|d?v[wh])|(?:^|\s)0(?=\s|$)|\b\d+fr\b/g, '');
      if (hasLiteral(structural)) findings.push({ ...d, reason: 'Unclassified visual literal' });
    }
  }
  for (const m of css.matchAll(/@(media|container)\s*([^{}]+)\{/g))
    if (/\d/.test(m[2]))
      findings.push({ property: '@' + m[1], value: m[2].trim(), line: lineAt(css, m.index), reason: 'Responsive structural threshold' });
  return findings;
}
const namedConstant = /^\s*(?:export\s+)?const\s+[A-Z][A-Z0-9_]*\s*(?::[^=]+)?=\s*-?(?:\d*\.)?\d+\s*;?\s*$/;
const INDEX_OR_COUNT_SOURCE =
  '\\[(?:\\d+|[a-zA-Z_$][\\w$]*\\s*[-+]\\s*\\d+)\\]|\\.(?:at|slice|splice|charAt|padStart|padEnd|toFixed|repeat)\\(-?\\d+[^)]*\\)|\\.(?:length|size)\\s*(?:[-+]\\s*\\d+|[<>=!]=+\\s*\\d+)|[<>=!]==?\\s*\\d+|\\b(?:i|j|n|index|depth|pass|attempt)\\s*[-+<>=]+\\s*\\d+|\\bfor\\s*\\(|ES\\d+|\\bMath\\.\\w+\\(|\\b0\\b|\\b1\\b|\\b2\\b';
const indexOrCount = () => new RegExp(INDEX_OR_COUNT_SOURCE, 'g');

const bareNumber = /(?:^|[^\w.$'"`-])(?:\d*\.)?\d+(?![\w.$'"`-])/;

export function auditRuntime(source, tokens) {
  const findings = [];
  source.split('\n').forEach((value, i) => {
    const code = value.replace(/'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|`(?:\\.|[^`\\])*`/g, '');
    if (namedConstant.test(code)) return;
    const bare = code.replace(indexOrCount(), '').match(bareNumber);
    if (bare)
      findings.push({
        property: 'unnamed-constant',
        value: value.trim(),
        line: i + 1,
        reason: 'Numeric literal outside a named constant declaration',
      });
  });
  const keyword =
    /^(?:['"`](?:auto|none|block|flex|grid|absolute|relative|fixed|hidden|visible|all|stroke|pointer|transparent|currentColor|var\([^`'"]+\))['"`]|true|false)$/;
  const derived = /\$\{[^}]*\}|\b(?:tokenNumber|tokenValue|paint|metric)\s*\([^)]*\)|var\(--kb-[\w-]+(?:\s*,[^)]*)?\)/g;
  const add = (m, property, value) => {
    const trimmed = value.trim();
    if (unknownRefs(value, tokens).length) {
      findings.push({ property, value: trimmed, line: lineAt(source, m.index), reason: 'Unknown token' });
      return;
    }
    if (fallbackLiterals(value, property).length) {
      findings.push({ property, value: trimmed, line: lineAt(source, m.index), reason: 'Literal in a var fallback' });
      return;
    }
    if (runtimeDeclarations(property, value).some((declared) => namesLiteralColor(declared.property, declared.value))) {
      findings.push({ property, value: trimmed, line: lineAt(source, m.index), reason: 'Literal named color' });
      return;
    }
    if (keyword.test(trimmed)) return;
    const residue = trimmed.replace(derived, '').replace(indexOrCount(), '');
    if (/\d/.test(residue) || /#[0-9a-f]{3,8}\b/i.test(residue))
      findings.push({
        property,
        value: trimmed,
        line: lineAt(source, m.index),
        reason: 'Runtime presentation requires token or exact geometry classification',
      });
  };
  for (const m of source.matchAll(/\.style\.([\w]+)\s*=\s*([^;]+);/g)) add(m, m[1], m[2]);
  for (const m of source.matchAll(/\.style\s*=\s*([^;]+);/g)) add(m, 'style', m[1]);
  for (const m of source.matchAll(/\.style\[(['"])([^'"]+)\1\]\s*=\s*([^;]+);/g)) add(m, m[2], m[3]);
  for (const m of source.matchAll(/\.style\.setProperty\(\s*(['"])([^'"]+)\1\s*,\s*([^;\n]+)\);/g)) add(m, m[2], m[3]);
  for (const m of source.matchAll(
    /\.setAttribute\(\s*(['"])(style|font-size|font-family|font-weight|stroke-width|stroke-dasharray|opacity|fill|stroke|rx|ry|width|height|x|y|transform|viewBox)\1\s*,\s*([^;]+?)\);/g,
  ))
    add(m, 'svg:' + m[2], m[3]);
  for (const m of source.matchAll(/Object\.assign\([^;]*?\.style\s*,\s*\{([^;]+?)\}\)/g)) add(m, 'style-object', m[1]);
  for (const m of source.matchAll(/style=(['"])(.*?)\1/g))
    for (const d of auditCSS('x{' + m[2] + '}', tokens))
      findings.push({ ...d, line: lineAt(source, m.index), property: 'inline:' + d.property });
  for (const m of source.matchAll(/\b(font-size|stroke-width|stroke-dasharray|opacity|fill|stroke|rx|ry)=(['"])(.*?)\2/g))
    add(m, 'markup:' + m[1], JSON.stringify(m[3]));
  return findings;
}
const NON_EXEMPTIBLE_REASONS = [
  'Unknown token',
  'Canonical redeclaration',
  'Literal named color',
  'Literal in a var fallback',
  'Border width follows the camera',
];
export const findingKey = (f) => JSON.stringify([f.file, f.property, f.value]);
export function validateExceptions(findings, exceptions) {
  const errors = [],
    actual = new Set(findings.map(findingKey)),
    allowed = new Set();
  for (const e of exceptions) {
    const key = findingKey(e);
    if (!e.reason?.trim()) errors.push('Unexplained exception ' + key);
    if (allowed.has(key)) errors.push('Duplicate exception ' + key);
    allowed.add(key);
    if (!actual.has(key)) errors.push('Unused exception ' + key);
    if (/^(?:["']?\d+(?:\.\d+)?px["']?)$/.test(e.value) && !['top', 'left', 'right', 'bottom'].includes(e.property))
      errors.push('Fixed visual size cannot be excepted: ' + key);
  }
  for (const f of findings)
    if (NON_EXEMPTIBLE_REASONS.includes(f.reason)) errors.push('Non-exemptible authority violation: ' + findingKey(f));
  for (const f of findings) if (!allowed.has(findingKey(f))) errors.push(`${f.file}:${f.line} ${f.property}: ${f.value}`);
  return errors;
}

const TOKEN_NUMBER_CALL = /(?<![\w$.])tokenNumber\(/g;
const TOKEN_NAME = /--[\w-]+/g;

export function themeDependentTokens(tokens) {
  return Object.keys(tokens).filter((name) => resolveAliases(tokens, tokens[name]?.value ?? '').includes('light-dark('));
}

export function auditThemeNumbers(source, tokens) {
  const themeDependent = new Set(themeDependentTokens(tokens));
  const findings = [];
  for (const match of source.matchAll(TOKEN_NUMBER_CALL)) {
    const close = closingParen(source, match.index + match[0].length - 1);
    if (close === -1) continue;
    const argument = source.slice(match.index + match[0].length, close);
    for (const name of new Set(argument.match(TOKEN_NAME) ?? []))
      if (themeDependent.has(name)) findings.push({ token: name, line: lineAt(source, match.index) });
  }
  return findings;
}

const nameSuffixes = (tokens, name) =>
  new Set(quantities(resolveAliases(tokens, tokens[name]?.value ?? '')).map((quantity) => '-' + quantity.text.replace('.', '-')));

export function valueNamedTokens(tokens) {
  return Object.keys(tokens).filter((name) => [...nameSuffixes(tokens, name)].some((suffix) => name.endsWith(suffix)));
}

const ROLE_GROUP_LABEL =
  /(?:^|[\s—-])(?:scale|ladder|ramp|palette|set)(?=\s*(?:[;,.—-]|step\b|$))|preserved baseline role|consumer inventory|#kb-board/i;
export function auditRoles(tokens) {
  const errors = [];
  const claimed = new Map();
  for (const [name, token] of Object.entries(tokens)) {
    const role = token.role?.trim() ?? '';
    if (ROLE_GROUP_LABEL.test(role)) errors.push(`${name} names a group rather than a purpose: ${role}`);
    const first = claimed.get(role);
    if (first) errors.push(`${name} repeats the role of ${first}: ${role}`);
    else claimed.set(role, name);
  }
  return errors;
}

const LADDER_STEP = /^-?(?:\d+(?:\.\d+)?|\.\d+)(?:px)?$/;

export function auditLadders(roles) {
  const errors = [];
  for (const [group, entries] of Object.entries(roles ?? {})) {
    const base = entries[BASE];
    if (typeof base !== 'number') continue;
    const fineWork = new Set(entries[FINE_WORK] ?? []);
    for (const leaf of tokenLeaves(entries)) {
      const value = entries[leaf]?.value?.trim() ?? '';
      if (!LADDER_STEP.test(value)) continue;
      const step = Math.abs(parseFloat(value));
      if (fineWork.has(step) || Number.isInteger(step / base)) continue;
      errors.push(`--kb-${group}-${leaf} is ${value}, which the ${group} ladder neither steps by ${base} nor lists as fine work`);
    }
  }
  return errors;
}

const ZOOM_GROWTH = /^--kb-[\w-]+-zoom-growth$/;
const WHOLE_DOCK_STEPS = /^(?:0|[1-9]\d*)$/;

export function auditZoomGrowth(tokens) {
  const findings = [];
  for (const [name, token] of Object.entries(tokens)) {
    if (!ZOOM_GROWTH.test(name)) continue;
    const steps = resolveAliases(tokens, token.value ?? '').trim();
    if (WHOLE_DOCK_STEPS.test(steps)) continue;
    findings.push(`${name} grows by ${steps}, which is not a whole number of dock zoom steps`);
  }
  return findings;
}

export function auditValueNames(tokens) {
  return valueNamedTokens(tokens).map((name) => `${name} carries its own value in its name, so the value cannot change without a rename`);
}
