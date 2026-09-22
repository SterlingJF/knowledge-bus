import { type Rect, type Point, contains, expand, intersects, union } from './geometry';
import { grow } from './camera';
import { tokenNumber } from './tokens';

export interface PlacedLabel {
  edge: string;
  text: string;
  numeric: boolean;
  anchor: Point;
  box: Rect;
}

const SAMPLE_COUNT = 41;
const CARD_CLEARANCE = 8;
const OFFSET_LADDER = 9;
const OFFSET_FIRST = 1;
const OFFSET_GROWTH = 1.5;
const OFFSET_RUNGS = Array.from({ length: OFFSET_LADDER }, (_, step) => (step ? OFFSET_FIRST * OFFSET_GROWTH ** (step - 1) : 0));
const OFFSET_DIRECTIONS = [
  { x: 0, y: -1 },
  { x: 0, y: 1 },
  { x: -1, y: 0 },
  { x: 1, y: 0 },
];

export interface LabelCandidate {
  edge: string;
  text: string;
  numeric: boolean;
  samples: Point[];
  middle: Point;
}

export function labelBox(text: string, centre: Point, zoom: number): Rect {
  const scale = grow(zoom, '--kb-label-zoom-growth');
  const w = (text.length * tokenNumber('--kb-label-char-width') + tokenNumber('--kb-connection-label-padding')) * scale;
  const h = tokenNumber('--kb-connection-label-height') * scale;
  return { x: centre.x - w / 2, y: centre.y - h / 2, w, h };
}

export interface HorizontalRail {
  x: number;
  y: number;
  w: number;
}

const penetrationDepth = (box: Rect, into: Rect): number =>
  intersects(box, into) ? Math.min(box.x + box.w - into.x, into.x + into.w - box.x, box.y + box.h - into.y, into.y + into.h - box.y) : 0;

const straddles = (box: Rect, rail: HorizontalRail): boolean =>
  box.y < rail.y && box.y + box.h > rail.y && box.x < rail.x + rail.w && box.x + box.w > rail.x;

export function placeLabels(
  candidates: LabelCandidate[],
  obstacles: Rect[],
  zoom: number,
  crossings: Point[] = [],
  rails: HorizontalRail[] = [],
): PlacedLabel[] {
  const occupied: Rect[] = obstacles.map((r) => expand(r, CARD_CLEARANCE));
  const placed: PlacedLabel[] = [];
  for (const candidate of [...candidates].sort((a, b) => (a.edge + a.text).localeCompare(b.edge + b.text))) {
    const plate = labelBox(candidate.text, { x: 0, y: 0 }, zoom);
    const step = plate.h;
    const farthest = OFFSET_RUNGS[OFFSET_RUNGS.length - 1] * step;
    const within = expand(union(candidate.samples.map((p) => ({ x: p.x, y: p.y, w: 0, h: 0 }))), farthest + plate.w);
    const nearby = occupied.filter((o) => intersects(o, within));
    const nearbyRails = rails.filter((rail) => intersects({ x: rail.x, y: rail.y, w: rail.w, h: 1 }, within));
    const nearbyCrossings = crossings.filter((c) => contains(within, { x: c.x, y: c.y, w: 0, h: 0 }));
    const scored = candidate.samples.flatMap((point) =>
      OFFSET_RUNGS.flatMap((rung) =>
        (rung ? OFFSET_DIRECTIONS : [{ x: 0, y: 0 }]).map((direction) => {
          const centre = { x: point.x + direction.x * rung * step, y: point.y + direction.y * rung * step };
          const shown = labelBox(candidate.text, centre, zoom);
          return {
            point,
            shown,
            rung,
            blocked: nearby.reduce((deepest, o) => Math.max(deepest, penetrationDepth(shown, o)), 0),
            straddle: nearbyRails.filter((rail) => straddles(shown, rail)).length,
            covered: nearbyCrossings.filter((c) => c.x >= shown.x && c.x <= shown.x + shown.w && c.y >= shown.y && c.y <= shown.y + shown.h)
              .length,
            reach: Math.hypot(point.x - candidate.middle.x, point.y - candidate.middle.y),
          };
        }),
      ),
    );
    const chosen = scored.sort(
      (a, b) => a.blocked - b.blocked || a.straddle - b.straddle || a.covered - b.covered || a.rung - b.rung || a.reach - b.reach,
    )[0];
    if (!chosen) continue;
    occupied.push(expand(chosen.shown, CARD_CLEARANCE));
    placed.push({
      edge: candidate.edge,
      text: candidate.text,
      numeric: candidate.numeric,
      anchor: chosen.point,
      box: chosen.shown,
    });
  }
  return placed;
}

export const sampleCount = () => SAMPLE_COUNT;
