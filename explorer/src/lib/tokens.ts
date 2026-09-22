import authority from '@/styles/visual-tokens.json';

type TokenRecord = { kind: string; value: string; role: string };
type Roles = typeof authority.roles;
type Parts = typeof authority.parts;
type Named<T> = Extract<keyof T, string>;
type TokenLeaves<T> = { [K in Named<T>]: T[K] extends { value: string } ? K : never }[Named<T>];
type PaletteName = `--kb-${TokenLeaves<Roles['color']>}`;
type LadderName = { [G in Exclude<Named<Roles>, 'color'>]: `--kb-${G}-${TokenLeaves<Roles[G]>}` }[Exclude<Named<Roles>, 'color'>];
type PartName = { [P in Named<Parts>]: `--kb-${P}-${TokenLeaves<Parts[P]>}` }[Named<Parts>];

const PALETTE = 'color';
const declaresToken = (leaf: unknown): leaf is TokenRecord => leaf !== null && typeof leaf === 'object' && !Array.isArray(leaf);

function flattenAuthority(): Record<string, TokenRecord> {
  const flat: Record<string, TokenRecord> = {};
  const groups = authority.roles as unknown as Record<string, Record<string, unknown>>;
  const parts = authority.parts as unknown as Record<string, Record<string, unknown>>;
  for (const [group, entries] of Object.entries(groups))
    for (const [leaf, token] of Object.entries(entries))
      if (declaresToken(token)) flat[group === PALETTE ? `--kb-${leaf}` : `--kb-${group}-${leaf}`] = token;
  for (const [part, entries] of Object.entries(parts))
    for (const [leaf, token] of Object.entries(entries)) if (declaresToken(token)) flat[`--kb-${part}-${leaf}`] = token;
  return flat;
}

const tokens = flattenAuthority();

export type TokenName = PaletteName | LadderName | PartName;
export type Theme = 'light' | 'dark';

export const tokenNames = Object.keys(tokens) as TokenName[];

export function tokenValue(name: TokenName): string {
  const token = tokens[name as string];
  if (!token) throw new Error('Missing visual token ' + String(name));
  return token.value;
}

const ALIAS = /^var\(\s*(--[\w-]+)\s*\)$/;
const NESTED_ALIAS = /var\((--[\w-]+)(?:\s*,[^)]*)?\)/g;
const ALIAS_HOPS = 20;
const THEME_SPLIT = 'light-dark(';
const numbers = new Map<string, number>();

const flattenWith = (source: Record<string, string>, value: string, depth = 0): string =>
  depth > ALIAS_HOPS
    ? value
    : value.replace(NESTED_ALIAS, (whole, name: string) =>
        source[name] === undefined ? whole : flattenWith(source, source[name], depth + 1),
      );

const rawValues: Record<string, string> = Object.fromEntries(Object.entries(tokens).map(([name, token]) => [name, token.value]));

function themeIndependent(name: TokenName, value: string): string {
  if (flattenWith(rawValues, value).includes(THEME_SPLIT))
    throw new Error('Theme-dependent visual token ' + String(name) + ' has no one number to read');
  return value;
}

export function tokenNumber(name: TokenName): number {
  const cached = numbers.get(name as string);
  if (cached !== undefined) return cached;
  let resolved = themeIndependent(name, tokenValue(name));
  for (let depth = 0; depth < ALIAS_HOPS; depth += 1) {
    const alias = resolved.match(ALIAS);
    if (!alias) break;
    resolved = themeIndependent(name, tokenValue(alias[1] as TokenName));
  }
  const value = parseFloat(resolved);
  if (!Number.isFinite(value)) throw new Error('Non-numeric visual token ' + String(name));
  numbers.set(name as string, value);
  return value;
}

function resolveTheme(value: string, theme: Theme): string {
  const pair = value.match(/^light-dark\(([^,]+),([^)]+)\)$/);
  return pair ? pair[theme === 'light' ? 1 : 2].trim() : value;
}

export function themeValues(theme: Theme): Record<string, string> {
  const resolved: Record<string, string> = {};
  for (const [name, token] of Object.entries(tokens)) resolved[name] = resolveTheme(token.value, theme);
  for (const name of Object.keys(resolved)) resolved[name] = flattenWith(resolved, resolved[name]);
  return resolved;
}

export function tokenCss(selector = '.shell'): string {
  return (
    selector +
    '{' +
    Object.entries(tokens)
      .map(([name, token]) => `${name}:${token.value}`)
      .join(';') +
    '}'
  );
}

export function exportThemeCss(selector: string, theme: 'auto' | Theme = 'auto'): string {
  const declarations = (t: Theme) =>
    Object.entries(themeValues(t))
      .map(([name, value]) => `${name}:${value}`)
      .join(';');
  const base = `${selector}{${declarations(theme === 'light' ? 'light' : 'dark')}}`;
  if (theme !== 'auto') return base;
  return `${base}@media(prefers-color-scheme:light){${selector}{${declarations('light')}}}`;
}
