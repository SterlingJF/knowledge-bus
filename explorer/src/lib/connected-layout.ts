const COLUMNS = 5;
const SLOT_X = 340;
const SLOT_Y = 240;
const ORIGIN_X = 60;
const ORIGIN_Y = 70;
const MAX_PASSES = 30;

export function connectedLayout(ids: string[], edges: { from: string; to: string }[]) {
  const slots = ids.map((_, i) => ({ x: ORIGIN_X + (i % COLUMNS) * SLOT_X, y: ORIGIN_Y + Math.floor(i / COLUMNS) * SLOT_Y }));
  const order = [...ids].sort();
  const weights = new Map<string, number>();
  for (const e of edges) {
    if (e.from === e.to || !ids.includes(e.from) || !ids.includes(e.to)) continue;
    weights.set(JSON.stringify([e.from, e.to].sort()), 1);
  }
  const pairs = [...weights.keys()].map((k) => JSON.parse(k) as [string, string]);
  const cost = () => {
    const pos = new Map(order.map((id, i) => [id, slots[i]]));
    return pairs.reduce((n, [a, b]) => n + Math.abs(pos.get(a)!.x - pos.get(b)!.x) + Math.abs(pos.get(a)!.y - pos.get(b)!.y), 0);
  };
  let score = cost();
  for (let pass = 0; pass < MAX_PASSES; pass += 1) {
    let best = score;
    let swap: [number, number] | null = null;
    for (let i = 0; i < order.length; i += 1)
      for (let j = i + 1; j < order.length; j += 1) {
        [order[i], order[j]] = [order[j], order[i]];
        const c = cost();
        [order[i], order[j]] = [order[j], order[i]];
        if (c < best) {
          best = c;
          swap = [i, j];
        }
      }
    if (!swap) break;
    const [i, j] = swap;
    [order[i], order[j]] = [order[j], order[i]];
    score = best;
  }
  return new Map(order.map((id, i) => [id, slots[i]]));
}
