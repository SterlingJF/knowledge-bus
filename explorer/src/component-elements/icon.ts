import { paths, ICON_GRID, MONOGRAM_TYPE_SIZE, type Mark } from '../lib/icons';

const SVG = 'http://www.w3.org/2000/svg';

function iconFrame(label?: string): SVGSVGElement {
  const svg = document.createElementNS(SVG, 'svg');
  svg.setAttribute('viewBox', `0 0 ${ICON_GRID} ${ICON_GRID}`);
  svg.setAttribute('class', 'icon');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  if (label) {
    svg.setAttribute('role', 'img');
    const title = document.createElementNS(SVG, 'title');
    title.textContent = label;
    svg.append(title);
  } else svg.setAttribute('aria-hidden', 'true');
  return svg;
}

function drawnPath(data: string): SVGPathElement {
  const path = document.createElementNS(SVG, 'path');
  path.setAttribute('d', data);
  return path;
}

function drawnMonogram(letters: string): SVGTextElement {
  const text = document.createElementNS(SVG, 'text');
  text.setAttribute('x', String(ICON_GRID / 2));
  text.setAttribute('y', String(ICON_GRID / 2));
  text.setAttribute('font-size', String(MONOGRAM_TYPE_SIZE));
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('dominant-baseline', 'central');
  text.setAttribute('fill', 'currentColor');
  text.setAttribute('stroke', 'none');
  text.textContent = letters;
  return text;
}

export function icon(name: string, label?: string): SVGSVGElement {
  const svg = iconFrame(label);
  svg.append(drawnPath(paths[name] ?? paths.frame));
  return svg;
}

export function markIcon(mark: Mark, label?: string): SVGSVGElement {
  const svg = iconFrame(label);
  svg.append('monogram' in mark ? drawnMonogram(mark.monogram) : drawnPath(mark.glyph));
  return svg;
}
