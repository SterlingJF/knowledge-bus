import { iconButton } from '../component-elements/icon-button';
import { type Scene } from '../lib/scene';
import { type Camera } from '../lib/model';
import { type Point } from '../lib/geometry';
import { tokenNumber } from '../lib/tokens';

const SVG = 'http://www.w3.org/2000/svg';

export interface Minimap {
  root: HTMLElement;
  update(camera: Camera, viewport: { width: number; height: number }): void;
  keepWithin(): void;
}

export function minimap(scene: Scene, navigate: (delta: Point) => void, jumpTo: (point: Point) => void, close: () => void): Minimap {
  const root = document.createElement('aside');
  root.className = 'panel minimap';
  root.setAttribute('aria-label', 'Map overview');
  const head = document.createElement('div');
  head.className = 'minimap-head';
  head.title = 'Drag to move the minimap';
  const title = document.createElement('strong');
  title.textContent = 'Map';
  const closeButton = iconButton('close', 'Close map overview', close);
  closeButton.classList.add('close');
  head.append(title, closeButton);
  const plot = document.createElementNS(SVG, 'svg');
  plot.classList.add('plot');
  const pad = tokenNumber('--kb-scene-margin');
  const box = { x: scene.bounds.x - pad, y: scene.bounds.y - pad, w: scene.bounds.w + pad * 2, h: scene.bounds.h + pad * 2 };
  plot.setAttribute('viewBox', `${box.x} ${box.y} ${box.w} ${box.h}`);
  plot.setAttribute('preserveAspectRatio', 'none');
  plot.setAttribute('role', 'img');
  plot.setAttribute('aria-label', 'Map overview; drag to move the view');
  for (const card of scene.layout.cards) {
    const rect = document.createElementNS(SVG, 'rect');
    rect.setAttribute('x', String(card.x));
    rect.setAttribute('y', String(card.y));
    rect.setAttribute('width', String(card.w));
    rect.setAttribute('height', String(card.h));
    rect.dataset.kind = card.kind;
    plot.append(rect);
  }
  const view = document.createElementNS(SVG, 'rect');
  view.dataset.camera = 'true';
  plot.append(view);
  const hintText = document.createElement('p');
  hintText.className = 'minimap-hint';
  hintText.textContent = 'Click or drag to move the view';
  root.append(head, plot, hintText);

  let plotDrag: { x: number; y: number } | null = null;
  const scaleOf = () => {
    const rect = plot.getBoundingClientRect();
    return { x: box.w / rect.width, y: box.h / rect.height, rect };
  };
  plot.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    event.stopPropagation();
    plot.setPointerCapture(event.pointerId);
    plotDrag = { x: event.clientX, y: event.clientY };
  });
  plot.addEventListener('pointermove', (event) => {
    if (!plotDrag) return;
    event.stopPropagation();
    const scale = scaleOf();
    navigate({ x: (event.clientX - plotDrag.x) * scale.x, y: (event.clientY - plotDrag.y) * scale.y });
    plotDrag = { x: event.clientX, y: event.clientY };
  });
  plot.addEventListener('click', (event) => {
    event.stopPropagation();
    const scale = scaleOf();
    jumpTo({ x: box.x + (event.clientX - scale.rect.left) * scale.x, y: box.y + (event.clientY - scale.rect.top) * scale.y });
  });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture'])
    plot.addEventListener(type, () => {
      plotDrag = null;
    });

  let move: { x: number; y: number; left: number; top: number } | null = null;
  const clearance = tokenNumber('--kb-minimap-clearance');
  const place = (left: number, top: number) => {
    const parent = root.offsetParent as HTMLElement | null;
    if (!parent) return;
    root.style.left = `${Math.max(clearance, Math.min(left, parent.clientWidth - root.offsetWidth - clearance))}px`;
    root.style.top = `${Math.max(clearance, Math.min(top, parent.clientHeight - root.offsetHeight - clearance))}px`;
    root.style.right = 'auto';
    root.style.bottom = 'auto';
  };
  head.addEventListener('pointerdown', (event) => {
    if ((event.target as Element).closest('button') || event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    move = { x: event.clientX, y: event.clientY, left: root.offsetLeft, top: root.offsetTop };
    head.setPointerCapture(event.pointerId);
    root.dataset.dragging = 'true';
  });
  head.addEventListener('pointermove', (event) => {
    if (!move) return;
    event.stopPropagation();
    place(move.left + event.clientX - move.x, move.top + event.clientY - move.y);
  });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture'])
    head.addEventListener(type, () => {
      move = null;
      delete root.dataset.dragging;
    });

  return {
    root,
    update(camera, viewport) {
      view.setAttribute('x', String(-camera.x / camera.z));
      view.setAttribute('y', String(-camera.y / camera.z));
      view.setAttribute('width', String(viewport.width / camera.z));
      view.setAttribute('height', String(viewport.height / camera.z));
    },
    keepWithin() {
      if (root.style.left) place(root.offsetLeft, root.offsetTop);
    },
  };
}
