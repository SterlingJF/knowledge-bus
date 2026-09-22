import { type Scene } from './scene';
import { type ExplorerModel, byId, human } from './model';
import { type PlacedCard, type Boundary, type Note } from './layout';
import { tokenNumber, exportThemeCss, type Theme } from './tokens';
import { ICON_GRID, MONOGRAM_TYPE_SIZE, type Mark } from './icons';
import { cardAnatomy, type CardAnatomy, type TextMeasurer, approximateText } from './card';

export type SvgTheme = 'auto' | Theme;
export interface SvgExportOptions {
  theme?: SvgTheme;
}

export const escapeXml = (value: unknown) =>
  String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[c]!);

const COORDINATE_PRECISION = 100;
const round = (n: number) => String(Math.round(n * COORDINATE_PRECISION) / COORDINATE_PRECISION);

const MAX_DISPLAY_COUNT = 9;
const DASH = { none: '', situational: '--kb-connection-dash-situational', mixed: '', frame: '--kb-connection-dash-frame' };
const MIXED_DASH = '12 3 3 3';

export function serializeSvg(
  scene: Scene,
  model: ExplorerModel,
  theme: SvgTheme = 'auto',
  measure: TextMeasurer = approximateText,
): string {
  const pad = tokenNumber('--kb-scene-margin');
  const b = scene.bounds;
  const width = b.w + pad * 2;
  const height = b.h + pad * 2;
  const paint = (name: string) => `var(${name})`;
  const out: string[] = [];

  const text = (x: number, y: number, value: string, size: number, fill: string, weight?: number, anchor?: string) =>
    `<text x="${round(x)}" y="${round(y)}" font-size="${round(size)}" fill="${fill}"${weight ? ` font-weight="${weight}"` : ''}${anchor ? ` text-anchor="${anchor}"` : ''}>${escapeXml(value)}</text>`;

  const drawn = (x: number, y: number, data: string, size: number, stroke: string) =>
    `<path d="${escapeXml(data)}" transform="translate(${round(x)} ${round(y)}) scale(${round(size / ICON_GRID)})" fill="none" stroke="${stroke}" stroke-width="${round((ICON_GRID / size) * tokenNumber('--kb-stroke-sm'))}" stroke-linecap="round" stroke-linejoin="round"/>`;

  const drawnMark = (x: number, y: number, mark: Mark, size: number, ink: string) =>
    'monogram' in mark
      ? `<text x="${round(x + size / 2)}" y="${round(y + size / 2)}" font-size="${round((size * MONOGRAM_TYPE_SIZE) / ICON_GRID)}" fill="${ink}" text-anchor="middle" dominant-baseline="central">${escapeXml(mark.monogram)}</text>`
      : drawn(x, y, mark.glyph, size, ink);

  out.push(
    `<rect x="${round(b.x - pad)}" y="${round(b.y - pad)}" width="${round(width)}" height="${round(height)}" fill="${paint('--kb-canvas')}"/>`,
  );

  const headingSize = tokenNumber('--kb-boundary-title-text');
  const captionSize = tokenNumber('--kb-type-body');
  const lineGap = tokenNumber('--kb-space-4');
  for (const boundary of scene.layout.boundaries as Boundary[]) {
    const stroke = boundary.role === 'scope' ? paint('--kb-boundary-scope-border') : paint('--kb-border');
    out.push(
      `<rect x="${round(boundary.x)}" y="${round(boundary.y)}" width="${round(boundary.w)}" height="${round(boundary.h)}" rx="${round(tokenNumber('--kb-radius-4xl'))}" fill="none" stroke="${stroke}"/>`,
    );
    if (boundary.title)
      out.push(
        text(
          boundary.x + tokenNumber('--kb-space-5'),
          boundary.y + tokenNumber('--kb-space-1-5'),
          boundary.title,
          headingSize,
          boundary.role === 'scope' ? paint('--kb-frame') : paint('--kb-text'),
          tokenNumber('--kb-weight-medium'),
        ),
      );
    if (boundary.caption)
      out.push(
        text(
          boundary.x + tokenNumber('--kb-space-5'),
          boundary.y + tokenNumber('--kb-boundary-caption-top') + lineGap,
          boundary.caption,
          captionSize,
          paint('--kb-text-muted'),
        ),
      );
  }

  for (const note of scene.layout.notes as Note[])
    out.push(text(note.x + note.w / 2, note.y + note.h / 2, note.text, captionSize, paint('--kb-text-muted'), undefined, 'middle'));

  const strokeBase = tokenNumber('--kb-connection-stroke-base');
  for (const edge of scene.edges) {
    if (!edge.drawn) continue;
    const stroke =
      edge.paint === 'rolled' ? paint('--kb-connection-rolled') : edge.paint === 'frame' ? paint('--kb-frame') : paint('--kb-element');
    const dashToken = DASH[edge.dash];
    const dash = edge.dash === 'mixed' ? MIXED_DASH : dashToken ? `var(${dashToken})` : '';
    out.push(
      `<path d="${edge.d}" fill="none" stroke="${stroke}" stroke-width="${round(strokeBase)}"${dash ? ` stroke-dasharray="${dash}"` : ''} opacity="${round(tokenNumber('--kb-connection-opacity-normal'))}"/>`,
    );
    if (edge.ordered && edge.points.length > 1) {
      const end = edge.points[edge.points.length - 1];
      const before = edge.points[edge.points.length - 2];
      const dx = Math.sign(end.x - before.x);
      const dy = Math.sign(end.y - before.y) || (dx ? 0 : 1);
      const size = tokenNumber('--kb-space-2');
      const tip = dy
        ? [end, { x: end.x - size / 2, y: end.y - dy * size }, { x: end.x + size / 2, y: end.y - dy * size }]
        : [end, { x: end.x - dx * size, y: end.y - size / 2 }, { x: end.x - dx * size, y: end.y + size / 2 }];
      out.push(`<polygon points="${tip.map((p) => `${round(p.x)},${round(p.y)}`).join(' ')}" fill="${stroke}"/>`);
    }
  }

  const labelHeight = tokenNumber('--kb-connection-label-height');
  const named = byId(model);
  const nameOf = (id: string): string => named.get(id)?.label ?? human(id.split(':').pop() ?? id);
  const endsOfEachEdge = new Map<string, string>();
  for (const edge of scene.edges)
    endsOfEachEdge.set(
      edge.path,
      edge.targetPair
        ? `${nameOf(edge.from)} \u00b7 ${nameOf(edge.targetPair[0])} and ${nameOf(edge.targetPair[1])}`
        : `${nameOf(edge.from)} \u00b7 ${nameOf(edge.to)}`,
    );
  for (const label of scene.labels) {
    out.push(`<g><title>${escapeXml(endsOfEachEdge.get(label.edge) ?? '')}</title>`);
    out.push(
      `<rect x="${round(label.box.x)}" y="${round(label.box.y)}" width="${round(label.box.w)}" height="${round(label.box.h)}" rx="${round(tokenNumber('--kb-radius-xs'))}" fill="${paint('--kb-canvas')}"/>`,
    );
    out.push(
      text(
        label.box.x + label.box.w / 2,
        label.box.y + labelHeight / 2 + tokenNumber('--kb-connection-label-baseline-offset'),
        label.text,
        tokenNumber('--kb-type-body-sm'),
        paint('--kb-text'),
        undefined,
        'middle',
      ),
    );
    out.push('</g>');
  }

  for (const nub of scene.nubs) {
    if (!nub.inset)
      out.push(
        `<path d="M ${round(nub.from.x)} ${round(nub.from.y)} L ${round(nub.box.x + nub.box.w / 2)} ${round(nub.box.y + nub.box.h / 2)}" stroke="${paint('--kb-element')}" stroke-width="${round(tokenNumber('--kb-connection-stroke-nub'))}" fill="none"/>`,
      );
    out.push(
      `<rect x="${round(nub.box.x)}" y="${round(nub.box.y)}" width="${round(nub.box.w)}" height="${round(nub.box.h)}" rx="${round(tokenNumber('--kb-radius-2xl'))}" fill="${paint('--kb-canvas')}" stroke="${paint('--kb-border')}"/>`,
    );
    out.push(
      text(
        nub.box.x + nub.box.w / 2,
        nub.box.y + nub.box.h / 2 + tokenNumber('--kb-connection-label-baseline-offset'),
        nub.count > MAX_DISPLAY_COUNT ? `${MAX_DISPLAY_COUNT}+` : String(nub.count),
        tokenNumber('--kb-type-body-sm'),
        paint('--kb-text'),
        undefined,
        'middle',
      ),
    );
  }

  for (const card of scene.layout.cards as PlacedCard[]) {
    const anatomy: CardAnatomy = cardAnatomy(card, model, measure);
    const accent = paint(anatomy.accent);
    out.push(`<g data-entity="${escapeXml(card.id)}">`);
    out.push(
      `<rect x="${round(card.x)}" y="${round(card.y)}" width="${round(card.w)}" height="${round(card.h)}" rx="${round(tokenNumber('--kb-radius-md'))}" fill="${paint('--kb-surface')}" stroke="${paint('--kb-border')}"/>`,
    );
    if (anatomy.edge === 'top')
      out.push(
        `<rect x="${round(card.x)}" y="${round(card.y)}" width="${round(card.w)}" height="${round(tokenNumber('--kb-stroke-lg'))}" fill="${accent}"/>`,
      );
    else
      out.push(
        `<rect x="${round(card.x)}" y="${round(card.y)}" width="${round(tokenNumber('--kb-stroke-lg'))}" height="${round(card.h)}" fill="${accent}"/>`,
      );
    const padding = tokenNumber('--kb-space-3');
    const iconSize = tokenNumber('--kb-icon-base');
    let cursor = card.y + padding + tokenNumber('--kb-card-text');
    if (anatomy.icon) {
      out.push(drawnMark(card.x + padding, card.y + padding, anatomy.icon, iconSize, accent));
    }
    const textX = card.x + padding + (anatomy.icon ? iconSize + tokenNumber('--kb-space-2') : 0);
    for (const line of anatomy.titleLines) {
      out.push(text(textX, cursor, line, tokenNumber('--kb-card-text'), paint('--kb-text'), tokenNumber('--kb-weight-medium')));
      cursor += tokenNumber('--kb-space-4');
    }
    for (const line of anatomy.subtitleLines) {
      out.push(text(textX, cursor, line, tokenNumber('--kb-type-body-sm'), paint('--kb-text-muted')));
      cursor += tokenNumber('--kb-space-4');
    }
    if (anatomy.match)
      out.push(
        text(
          card.x + padding,
          card.y + card.h - padding,
          anatomy.match,
          tokenNumber('--kb-type-body-lg'),
          paint('--kb-text'),
          tokenNumber('--kb-weight-medium'),
        ),
      );
    anatomy.frameIcons.forEach((name, index) =>
      out.push(
        drawnMark(
          card.x + padding + index * (iconSize + tokenNumber('--kb-space-2')),
          card.y + card.h - padding - iconSize,
          name,
          iconSize,
          paint('--kb-frame'),
        ),
      ),
    );
    if (anatomy.overflow)
      out.push(
        text(
          card.x + padding + anatomy.frameIcons.length * (iconSize + tokenNumber('--kb-space-2')),
          card.y + card.h - padding,
          anatomy.overflow,
          tokenNumber('--kb-type-caption'),
          paint('--kb-text-muted'),
        ),
      );
    out.push('</g>');
  }

  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" style="display:block;width:100vw;height:100vh" viewBox="${round(b.x - pad)} ${round(b.y - pad)} ${round(width)} ${round(height)}" preserveAspectRatio="xMidYMid meet" role="img">` +
    `<title>${escapeXml(model.universe.label)}</title>` +
    `<desc>${escapeXml(`Knowledge Bus universe map: ${human(model.universe.id)}. Current presentation options; no transient selection.`)}</desc>` +
    `<style>${exportThemeCss('svg', theme)}text{font-family:var(--kb-font-sans)}</style>` +
    out.join('') +
    '</svg>'
  );
}
