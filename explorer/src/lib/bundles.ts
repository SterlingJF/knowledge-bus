import { type DisplayEdge } from './model';
import { collapseCardPairs } from './rollup';

export function bundleFocusCard(selected: string, hover: string, kind: string, connection: string): string {
  if (selected) return selected;
  if (connection.startsWith('bundle:')) return (JSON.parse(connection.slice(7)) as string[])[0];
  return connection || kind ? '' : hover;
}

export function bundleExpandedPairs(source: DisplayEdge[], id: string): DisplayEdge[] {
  if (!id) return source;
  const groups = new Map<string, DisplayEdge[]>();
  for (const edge of source) {
    if (edge.targetPair || edge.from === edge.to || (edge.from !== id && edge.to !== id)) continue;
    const other = edge.from === id ? edge.to : edge.from;
    if (!groups.has(other)) groups.set(other, []);
    groups.get(other)!.push(edge);
  }
  const replacements = new Map<DisplayEdge, DisplayEdge>();
  const removed = new Set<DisplayEdge>();
  for (const [other, members] of groups) {
    if (members.length < 2) continue;
    const [bundle] = collapseCardPairs(members.map((edge) => ({ ...edge, sources: [{ source: edge, composition: [] }] })));
    bundle.path = 'bundle:' + JSON.stringify([id, other]);
    bundle.bundled = true;
    replacements.set(members[0], bundle);
    members.slice(1).forEach((edge) => removed.add(edge));
  }
  return source.filter((edge) => !removed.has(edge)).map((edge) => replacements.get(edge) ?? edge);
}
