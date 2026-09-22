export interface Point {
  x: number;
  y: number;
}
export interface Rect extends Point {
  w: number;
  h: number;
}

export const union = (rects: Rect[]): Rect => {
  if (!rects.length) return { x: 0, y: 0, w: 1, h: 1 };
  const x = Math.min(...rects.map((r) => r.x));
  const y = Math.min(...rects.map((r) => r.y));
  return { x, y, w: Math.max(...rects.map((r) => r.x + r.w)) - x, h: Math.max(...rects.map((r) => r.y + r.h)) - y };
};

export const intersects = (a: Rect, b: Rect) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;

export const contains = (outer: Rect, inner: Rect) =>
  inner.x >= outer.x && inner.y >= outer.y && inner.x + inner.w <= outer.x + outer.w && inner.y + inner.h <= outer.y + outer.h;

export const expand = (r: Rect, by: number): Rect => ({ x: r.x - by, y: r.y - by, w: r.w + by * 2, h: r.h + by * 2 });

export const center = (r: Rect): Point => ({ x: r.x + r.w / 2, y: r.y + r.h / 2 });

export function polylineCrossings(lines: Point[][]): Point[] {
  const segments = lines.map((points) => points.slice(1).map((point, index) => ({ a: points[index], b: point })));
  const meeting = (s: { a: Point; b: Point }, t: { a: Point; b: Point }): Point | null => {
    const horizontal = s.a.y === s.b.y;
    if (horizontal === (t.a.y === t.b.y)) return null;
    const across = horizontal ? s : t;
    const down = horizontal ? t : s;
    const spans = (from: number, to: number, value: number) => value >= Math.min(from, to) && value <= Math.max(from, to);
    return spans(across.a.x, across.b.x, down.a.x) && spans(down.a.y, down.b.y, across.a.y) ? { x: down.a.x, y: across.a.y } : null;
  };
  const found: Point[] = [];
  for (let i = 0; i < segments.length; i += 1)
    for (let j = i + 1; j < segments.length; j += 1)
      for (const first of segments[i])
        for (const second of segments[j]) {
          const point = meeting(first, second);
          if (point) found.push(point);
        }
  return found;
}
