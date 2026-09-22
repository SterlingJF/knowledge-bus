import { type Rect, type Point } from './geometry';

export interface RouteEdge {
  from?: string;
  to?: string;
  kind?: string;
  strength?: string;
  label?: string;
}

const PORT_SPREAD = 7;
const PORT_STEP = 4;
const BASE_GAP = 20;
const CORNER_COST = 18;
const CONGESTION_TOLERANCE = 9;
const CONGESTION_WEIGHT = 8;
const LABEL_CHAR = 8;
const LABEL_PADDING = 24;
const LABEL_PENALTY = 400;
const HASH_MULTIPLIER = 31;

export type Segment = [Point, Point];

export class Router {
  private routed: Segment[] = [];

  begin() {
    this.routed = [];
  }

  path(a: Rect, b: Rect, rects: Map<string, Rect>, edge: RouteEdge = {}): string {
    const identity = [edge.from, edge.to, edge.kind, edge.strength].join('|');
    const hash = [...identity].reduce((n, c) => (n * HASH_MULTIPLIER + c.charCodeAt(0)) >>> 0, 0);
    const offset = ((hash % PORT_SPREAD) - (PORT_SPREAD - 1) / 2) * PORT_STEP;
    const gap = BASE_GAP + offset;
    const boxes = [...rects.values()].filter((r) => r.w > 0 && r.h > 0);
    const ports = (r: Rect): Segment[] => [
      [
        { x: r.x + r.w / 2 + offset, y: r.y },
        { x: r.x + r.w / 2 + offset, y: r.y - gap },
      ],
      [
        { x: r.x + r.w, y: r.y + r.h / 2 + offset },
        { x: r.x + r.w + gap, y: r.y + r.h / 2 + offset },
      ],
      [
        { x: r.x + r.w / 2 + offset, y: r.y + r.h },
        { x: r.x + r.w / 2 + offset, y: r.y + r.h + gap },
      ],
      [
        { x: r.x, y: r.y + r.h / 2 + offset },
        { x: r.x - gap, y: r.y + r.h / 2 + offset },
      ],
    ];
    const clear = (p: Point, q: Point) =>
      !boxes.some((r) =>
        p.x === q.x
          ? p.x > r.x && p.x < r.x + r.w && Math.max(p.y, q.y) > r.y && Math.min(p.y, q.y) < r.y + r.h
          : p.y > r.y && p.y < r.y + r.h && Math.max(p.x, q.x) > r.x && Math.min(p.x, q.x) < r.x + r.w,
      );
    const xs = [...new Set(boxes.flatMap((r) => [r.x - gap, r.x + r.w + gap]))].sort((x, y) => x - y);
    const ys = [...new Set(boxes.flatMap((r) => [r.y - gap, r.y + r.h + gap]))].sort((x, y) => x - y);
    const found: { points: Point[]; score: number } = { points: [], score: Infinity };
    const overlap = (lowA: number, highA: number, lowB: number, highB: number) =>
      Math.max(0, Math.min(highA, highB) - Math.max(lowA, lowB));
    const consider = (candidate: Point[]) => {
      const points = candidate.filter((p, i) => !i || p.x !== candidate[i - 1].x || p.y !== candidate[i - 1].y);
      if (points.some((p, i) => i && !clear(points[i - 1], p))) return;
      const congestion = points.reduce((sum, q, i) => {
        if (!i) return sum;
        const p = points[i - 1];
        return (
          sum +
          this.routed.reduce((n, [u, v]) => {
            if (p.x === q.x && u.x === v.x && Math.abs(p.x - u.x) < CONGESTION_TOLERANCE)
              return n + overlap(Math.min(p.y, q.y), Math.max(p.y, q.y), Math.min(u.y, v.y), Math.max(u.y, v.y)) * CONGESTION_WEIGHT;
            if (p.y === q.y && u.y === v.y && Math.abs(p.y - u.y) < CONGESTION_TOLERANCE)
              return n + overlap(Math.min(p.x, q.x), Math.max(p.x, q.x), Math.min(u.x, v.x), Math.max(u.x, v.x)) * CONGESTION_WEIGHT;
            return n;
          }, 0)
        );
      }, 0);
      const labelWidth = (edge.label || '').length * LABEL_CHAR + LABEL_PADDING;
      const labelRoom = points.some((p, i) => i && p.y === points[i - 1].y && Math.abs(p.x - points[i - 1].x) >= labelWidth);
      const length =
        points.reduce((n, p, i) => n + (i ? Math.abs(p.x - points[i - 1].x) + Math.abs(p.y - points[i - 1].y) : 0), 0) +
        points.length * CORNER_COST +
        congestion +
        (labelRoom ? 0 : LABEL_PENALTY);
      if (length < found.score) {
        found.score = length;
        found.points = points;
      }
    };
    for (const [start, p] of ports(a))
      for (const [end, q] of ports(b)) {
        for (const x of xs) consider([start, p, { x, y: p.y }, { x, y: q.y }, q, end]);
        for (const y of ys) consider([start, p, { x: p.x, y }, { x: q.x, y }, q, end]);
      }
    const chosen = found.points;
    const path = chosen.length
      ? 'M ' + chosen.map((p) => `${p.x} ${p.y}`).join(' L ')
      : `M ${a.x + a.w / 2} ${a.y + a.h} L ${a.x + a.w / 2} ${b.y - BASE_GAP} L ${b.x + b.w / 2} ${b.y - BASE_GAP} L ${b.x + b.w / 2} ${b.y}`;
    const segments: Segment[] = chosen.slice(1).map((p, i) => [chosen[i], p] as Segment);
    this.routed.push(...segments);
    return path;
  }
}
