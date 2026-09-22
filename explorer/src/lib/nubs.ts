import { type Rect, type Point } from './geometry';
import { tokenNumber } from './tokens';
import { grow } from './camera';

export interface PlacedNub {
  id: string;
  count: number;
  box: Rect;
  from: Point;
  inset: boolean;
}

const NUB_MARGIN = 2;
const INSET_OFFSET = 4;

export function placeNubs(
  counts: Map<string, number>,
  rects: Map<string, Rect>,
  scopes: Map<string, Rect>,
  heads: Rect[],
  zoom: number,
): PlacedNub[] {
  const scale = grow(zoom, '--kb-count-zoom-growth');
  const size = tokenNumber('--kb-count-size') * scale;
  const gap = tokenNumber('--kb-count-gap') * scale;
  const occupied: Rect[] = [];
  const placed: PlacedNub[] = [];
  const overlaps = (a: Point, b: Rect) =>
    a.x < b.x + b.w + NUB_MARGIN && a.x + size > b.x - NUB_MARGIN && a.y < b.y + b.h + NUB_MARGIN && a.y + size > b.y - NUB_MARGIN;
  for (const [id, count] of [...counts].sort(([a], [b]) => a.localeCompare(b))) {
    const r = rects.get(id);
    if (!r || !r.w || !r.h) continue;
    const cx = r.x + r.w / 2;
    const cy = r.y + r.h / 2;
    const candidates = [
      { x: r.x + r.w + gap, y: cy - size / 2, sx: r.x + r.w, sy: cy },
      { x: r.x - gap - size, y: cy - size / 2, sx: r.x, sy: cy },
      { x: cx - size / 2, y: r.y + r.h + gap, sx: cx, sy: r.y + r.h },
      { x: cx - size / 2, y: r.y - gap - size, sx: cx, sy: r.y },
    ];
    const scope = scopes.get(id);
    const inside = (p: Point) =>
      !scope || (p.x > scope.x && p.y > scope.y && p.x + size < scope.x + scope.w && p.y + size < scope.y + scope.h);
    const spot = candidates.find(
      (p) =>
        [...rects].every(([key, box]) => key === id || !overlaps(p, box)) &&
        occupied.every((box) => !overlaps(p, box)) &&
        heads.every((box) => !overlaps(p, box)) &&
        inside(p),
    );
    const chosen = spot ?? {
      x: r.x + r.w - size - INSET_OFFSET,
      y: r.y + r.h - size - INSET_OFFSET,
      sx: r.x + r.w,
      sy: r.y + r.h - size / 2 - INSET_OFFSET,
    };
    occupied.push({ x: chosen.x, y: chosen.y, w: size, h: size });
    placed.push({
      id,
      count,
      box: { x: chosen.x, y: chosen.y, w: size, h: size },
      from: { x: chosen.sx, y: chosen.sy },
      inset: !spot,
    });
  }
  return placed;
}
