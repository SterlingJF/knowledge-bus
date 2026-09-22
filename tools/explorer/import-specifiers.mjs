import { parseSync } from 'oxc-parser';
import path from 'node:path';

export function moduleSpecifiers(file, source) {
  const parsed = parseSync(file, source);
  if (parsed.errors.length) throw new Error(`${file}: ${parsed.errors[0].message}`);
  const specifiers = [];
  const pending = [parsed.program];
  while (pending.length) {
    const node = pending.pop();
    if (
      ['ImportDeclaration', 'ExportNamedDeclaration', 'ExportAllDeclaration', 'ImportExpression', 'TSImportType'].includes(node.type) &&
      node.source?.type === 'Literal' &&
      typeof node.source.value === 'string'
    )
      specifiers.push(node.source);
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) {
        for (const child of value) if (child && typeof child === 'object') pending.push(child);
      } else if (value && typeof value === 'object') pending.push(value);
    }
  }
  return specifiers;
}

export function relativeAliasSpecifiers(file, source, packageRoot) {
  const replacements = new Map();
  for (const specifier of moduleSpecifiers(file, source)) {
    if (!specifier.value.startsWith('@/')) continue;
    const target = path.resolve(packageRoot, specifier.value.slice(2));
    if (path.relative(packageRoot, target).split(path.sep)[0] === '..')
      throw new Error(`${file}: alias escapes its package: ${specifier.value}`);
    const relative = path.relative(path.dirname(file), target).split(path.sep).join('/');
    replacements.set(specifier.start, { end: specifier.end, value: `'${relative.startsWith('.') ? relative : './' + relative}'` });
  }
  const pieces = [];
  let start = 0;
  for (let offset = 0; offset < source.length; offset += 1) {
    const replacement = replacements.get(offset);
    if (!replacement) continue;
    pieces.push(source.slice(start, offset), replacement.value);
    start = replacement.end;
    offset = start - 1;
  }
  pieces.push(source.slice(start));
  return pieces.join('');
}
