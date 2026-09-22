import { type WireDrawing } from '../lib/connection-reading';
import { tokenNumber } from '../lib/tokens';

const SVG = 'http://www.w3.org/2000/svg';

function drawnWire(drawing: WireDrawing, reading: string): SVGSVGElement {
  const span = tokenNumber('--kb-size-sm');
  const height = tokenNumber('--kb-icon-base');
  const middle = height / 2;
  const svg = document.createElementNS(SVG, 'svg');
  svg.setAttribute('viewBox', `0 0 ${span} ${height}`);
  svg.setAttribute('class', 'glyph-wire');
  svg.setAttribute('role', 'img');
  const title = document.createElementNS(SVG, 'title');
  title.textContent = reading;
  svg.append(title);
  const wire = document.createElementNS(SVG, 'path');
  wire.setAttribute('d', `M 0 ${middle} L ${span} ${middle}`);
  wire.classList.add('wire');
  wire.dataset.paint = drawing.paint;
  wire.dataset.dash = drawing.requirement === 'situational' ? 'situational' : 'none';
  svg.append(wire);
  if (drawing.ordered) {
    const tip = tokenNumber('--kb-space-2');
    const head = document.createElementNS(SVG, 'polygon');
    head.setAttribute('points', `${span},${middle} ${span - tip},${middle - tip / 2} ${span - tip},${middle + tip / 2}`);
    head.classList.add('arrowhead');
    head.dataset.paint = drawing.paint;
    svg.append(head);
  }
  return svg;
}

export function holdingGlyph(holding: 'owns' | 'links'): SVGSVGElement {
  const side = tokenNumber('--kb-icon-base');
  const middle = side / 2;
  const svg = document.createElementNS(SVG, 'svg');
  svg.setAttribute('viewBox', `0 0 ${side} ${side}`);
  svg.setAttribute('class', 'holding-glyph');
  svg.setAttribute('aria-hidden', 'true');
  const mark = document.createElementNS(SVG, 'polygon');
  mark.setAttribute('points', `0,${middle / 2} ${side},${middle} 0,${middle + middle / 2}`);
  mark.dataset.holding = holding;
  svg.append(mark);
  return svg;
}

export function relationGlyph(drawing: WireDrawing, from: Node, to: Node, reading: string): HTMLElement {
  const glyph = document.createElement('div');
  glyph.className = 'relation-glyph';
  glyph.dataset.paint = drawing.paint;
  const target = document.createElement('span');
  target.className = 'glyph-target';
  target.append(drawnWire(drawing, reading), to);
  glyph.append(from, target);
  return glyph;
}
