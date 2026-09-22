import { type DisplayEdge, type CompositionEntry } from './model';

export type RollupMode = 'relations' | 'composition';

export function artifactEdges(
  source: DisplayEdge[],
  composition: CompositionEntry[],
  artifactIds: string[],
  mode: RollupMode,
): DisplayEdge[] {
  const artifacts = new Set(artifactIds);
  const members = new Map<string, CompositionEntry[]>();
  for (const entry of composition) {
    if (!members.has(entry.to)) members.set(entry.to, []);
    members.get(entry.to)!.push(entry);
  }
  const result: DisplayEdge[] = [];
  const add = (edge: DisplayEdge, from: string, to: string, via: CompositionEntry[]) => {
    if (from === to) return;
    result.push({
      ...edge,
      from,
      to,
      targetPair: undefined,
      rolled: via.length > 0,
      strength: via.some((x) => x.strength === 'situational') ? 'situational' : 'core',
      provenance: { source: edge, composition: via },
      path: edge.path + '|' + from + '|' + to,
      label: edge.label + (via.length ? ' · via ' + [...new Set(via.map((x) => x.to))].join(', ') : ''),
    });
  };
  if (mode === 'composition') {
    for (const [, entries] of members)
      for (let i = 0; i < entries.length; i += 1)
        for (let j = i + 1; j < entries.length; j += 1)
          add(
            { path: entries[i].path + '|' + entries[j].path, label: 'Shared element', ordered: false } as DisplayEdge,
            entries[i].from,
            entries[j].from,
            [entries[i], entries[j]],
          );
  } else {
    for (const edge of source) {
      const left = artifacts.has(edge.from)
        ? [{ from: edge.from } as CompositionEntry]
        : (members.get(edge.from) ?? [{ from: edge.from } as CompositionEntry]);
      const right = artifacts.has(edge.to)
        ? [{ from: edge.to } as CompositionEntry]
        : (members.get(edge.to) ?? [{ from: edge.to } as CompositionEntry]);
      for (const a of left)
        for (const b of right)
          add(
            edge,
            a.from,
            b.from,
            [a, b].filter((x) => x.path),
          );
    }
  }
  const groups = new Map<string, DisplayEdge>();
  for (const edge of result) {
    const pair = edge.ordered ? [edge.from, edge.to] : [edge.from, edge.to].sort();
    const key = JSON.stringify([pair, edge.kind || mode, edge.rolled, edge.strength]);
    if (!groups.has(key)) groups.set(key, { ...edge, from: pair[0], to: pair[1], sources: [] });
    groups.get(key)!.sources!.push(edge.provenance!);
  }
  return [...groups.values()].map((e) => ({ ...e, label: e.label.split(' · ')[0] }));
}

export function collapseCardPairs(edges: DisplayEdge[]): DisplayEdge[] {
  const groups = new Map<string, DisplayEdge[]>();
  for (const edge of edges) {
    const key = JSON.stringify([edge.from, edge.to].sort());
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(edge);
  }
  return [...groups.entries()].map(([key, members]) => {
    const [from, to] = JSON.parse(key) as [string, string];
    const directions = new Set(members.filter((e) => e.ordered).map((e) => (e.from === from ? 'forward' : 'reverse')));
    const mixedDirection = directions.size > 1 || (members.some((e) => !e.ordered) && directions.size > 0);
    const labels = [...new Set(members.map((e) => e.label))].sort();
    const strengths = [...new Set(members.map((e) => e.strength))];
    const rolls = new Set(members.map((e) => e.rolled));
    const reverse = !mixedDirection && directions.has('reverse');
    return {
      ...members[0],
      from: reverse ? to : from,
      to: reverse ? from : to,
      path: 'pair:' + key,
      label: labels.join(' · '),
      ordered: !mixedDirection && directions.size === 1,
      strength: strengths.length === 1 ? strengths[0] : 'mixed',
      rolled: members.some((e) => e.rolled),
      mixedRollup: rolls.size > 1,
      members,
      sources: members.flatMap((e) => e.sources ?? []),
    };
  });
}
