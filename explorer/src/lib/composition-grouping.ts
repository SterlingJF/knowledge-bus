import { compositionDetails } from './phrasing';

export type Holding = 'owns' | 'links';

export interface CompositionMember {
  target: string;
  answer?: string;
  from?: string;
  strength?: string;
  mode?: string;
  when?: unknown;
}

export interface CompositionRow {
  target: string;
  holding: Holding;
  destination: string | null;
  predicate: string | null;
}

export interface CompositionGroup {
  predicate: string;
  conditionTitle: string | null;
  fallback: string | null;
  when: unknown;
  rows: CompositionRow[];
}

export const holdingOf = (member: { mode?: string }): Holding => (member.mode === 'links' ? 'links' : 'owns');

export function answerOwners(entries: { from: string; to: string; mode?: string }[]): Map<string, string> {
  const owners = new Map<string, string>();
  for (const entry of entries) if (holdingOf(entry) === 'owns' && !owners.has(entry.to)) owners.set(entry.to, entry.from);
  return owners;
}

const conditionSignature = (when: unknown): string =>
  Object.entries((when ?? {}) as Record<string, unknown>)
    .map(([frame, value]): [string, string] => [frame, Array.isArray(value) ? [...value].map(String).sort().join('|') : String(value)])
    .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
    .map(([frame, value]) => `${frame}=${value}`)
    .join(';');

export function compositionGroups(members: CompositionMember[], owners: Map<string, string>): CompositionGroup[] {
  const groups = new Map<string, CompositionGroup>();
  const order: string[] = [];
  for (const member of members) {
    const copy = compositionDetails(member);
    const key = `${copy.requirement} ${conditionSignature(member.when)}`;
    let group = groups.get(key);
    if (!group) {
      group = { predicate: copy.requirement, conditionTitle: copy.conditionTitle, fallback: copy.fallback, when: member.when, rows: [] };
      groups.set(key, group);
      order.push(key);
    }
    const holding = holdingOf(member);
    group.rows.push({
      target: member.target,
      holding,
      destination: holding === 'links' ? (owners.get(member.answer ?? member.target) ?? null) : null,
      predicate: null,
    });
  }
  return order.map((key) => groups.get(key)!);
}
