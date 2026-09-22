import { type Camera } from './model';
import { type Rect } from './geometry';
import { tokenNumber } from './tokens';

export interface Insets {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export const noInsets = (): Insets => ({ left: 0, right: 0, top: 0, bottom: 0 });

export const MIN_ZOOM = 0.15;
export const MAX_ZOOM = 1.8;
const EDGE_PAD = 32;
const FIT_PAD_X = 64;
const FIT_PAD_Y = 100;
const FIT_OFFSET_Y = 60;
const SELECTION_PAD = 64;
const SELECTION_MAX_ZOOM = 1.2;
const SAFE_MARGIN = 20;

export const clampZoom = (z: number) => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, z));

export function constrainCamera(target: Camera, bounds: Rect, viewport: { width: number; height: number }, insets = noInsets()): Camera {
  const b = {
    x: bounds.x - insets.left / target.z,
    y: bounds.y - insets.top / target.z,
    w: bounds.w + (insets.left + insets.right) / target.z,
    h: bounds.h + (insets.top + insets.bottom) / target.z,
  };
  const clamp = (value: number, start: number, size: number, view: number) =>
    size * target.z <= view - EDGE_PAD * 2
      ? (view - size * target.z) / 2 - start * target.z
      : Math.max(view - EDGE_PAD - (start + size) * target.z, Math.min(EDGE_PAD - start * target.z, value));
  return {
    z: target.z,
    x: clamp(target.x, b.x, b.w, viewport.width),
    y: clamp(target.y, b.y, b.h, viewport.height),
  };
}

export function zoomAround(camera: Camera, z: number, cx: number, cy: number): Camera {
  const next = clampZoom(z);
  return { z: next, x: cx - (cx - camera.x) * (next / camera.z), y: cy - (cy - camera.y) * (next / camera.z) };
}

export function fitCamera(bounds: Rect, viewport: { width: number; height: number }): Camera {
  const z = Math.max(MIN_ZOOM, Math.min((viewport.width - FIT_PAD_X) / bounds.w, (viewport.height - FIT_PAD_Y) / bounds.h));
  return {
    z,
    x: (viewport.width - bounds.w * z) / 2 - bounds.x * z,
    y: (viewport.height - FIT_OFFSET_Y - bounds.h * z) / 2 - bounds.y * z,
  };
}

export function fitCameraWithin(bounds: Rect, viewport: { width: number; height: number }, insets: Insets): Camera {
  const safe = fitCamera(bounds, {
    width: viewport.width - insets.left - insets.right,
    height: viewport.height - insets.top - insets.bottom,
  });
  return { z: safe.z, x: safe.x + insets.left, y: safe.y + insets.top };
}

export function frameCamera(bounds: Rect, viewport: { width: number; height: number }, insets: Insets): Camera | null {
  const safe = {
    x: insets.left + SAFE_MARGIN,
    y: insets.top + SAFE_MARGIN,
    w: viewport.width - insets.left - insets.right - SAFE_MARGIN * 2,
    h: viewport.height - insets.top - insets.bottom - SAFE_MARGIN * 2,
  };
  if (safe.w <= 0 || safe.h <= 0) return null;
  const z = Math.min(SELECTION_MAX_ZOOM, safe.w / (bounds.w + SELECTION_PAD), safe.h / (bounds.h + SELECTION_PAD));
  return {
    z,
    x: safe.x + safe.w / 2 - (bounds.x + bounds.w / 2) * z,
    y: safe.y + safe.h / 2 - (bounds.y + bounds.h / 2) * z,
  };
}

const EASE_EXPONENT = 3;

export const easeOut = (fraction: number) => 1 - (1 - Math.min(1, Math.max(0, fraction))) ** EASE_EXPONENT;

export function interpolate(from: Camera, to: Camera, fraction: number): Camera {
  const eased = easeOut(fraction);
  return {
    x: from.x + (to.x - from.x) * eased,
    y: from.y + (to.y - from.y) * eased,
    z: from.z + (to.z - from.z) * eased,
  };
}

export const motionDuration = () => tokenNumber('--kb-motion-camera');

export type GrowthLimit =
  '--kb-heading-zoom-growth' | '--kb-card-heading-zoom-growth' | '--kb-label-zoom-growth' | '--kb-count-zoom-growth';

export const grow = (zoom: number, limit: GrowthLimit) =>
  Math.min(tokenNumber('--kb-zoom-step') ** tokenNumber(limit), Math.max(1, 1 / zoom));

export const boundaryScale = (zoom: number) => grow(zoom, '--kb-heading-zoom-growth');

export const cardHeadingScale = (zoom: number) => grow(zoom, '--kb-card-heading-zoom-growth');

export const labelScale = (zoom: number) => grow(zoom, '--kb-label-zoom-growth');
