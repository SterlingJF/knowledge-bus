import { entityCard, optionCard } from './entity-card';
import { markIcon } from '../component-elements/icon';
import { type Point, type Rect } from '../lib/geometry';
import { labelBox } from '../lib/labels';
import { type PlacedNub } from '../lib/nubs';
import { type Mark, marksOf } from '../lib/icons';
import { setCardState, type CardState } from '../component-elements/card-surface';
import { holdingDrawn, labelLayer, nubLayer, type Scene } from '../lib/scene';
import { emphasise, type CardEmphasis, type EdgeEmphasis } from '../lib/emphasis';
import { type ExplorerModel, type Camera, type Selection, byId, human } from '../lib/model';
import { type PlacedCard, roleOfTheBoundaryEachCardStandsIn } from '../lib/layout';
import { boundaryScale, cardHeadingScale, grow, labelScale } from '../lib/camera';
import { tokenNumber } from '../lib/tokens';
import { type TextMeasurer } from '../lib/card';

const SVG = 'http://www.w3.org/2000/svg';
const MAX_DISPLAY_COUNT = 9;
const DESCRIPTIONS_DRAWN_WITHIN_A_LINE_ALLOWANCE = ['frame', 'factor', 'option'];

export interface MapHandle {
  root: HTMLElement;
  applyCamera(camera: Camera): void;
  highlight(selection: Selection, hover: string): void;
  cardElement(id: string): HTMLElement | undefined;
  drawnBounds(): Rect;
}

export interface MapActions {
  selectEntity(id: string): void;
  selectConnection(path: string): void;
  hover(id: string): void;
}

function optionStats(model: ExplorerModel, optionId: string) {
  const ordering = model.orderingFrameId.split(':').slice(1).join(':');
  const value = optionId.split(':').pop();
  const elements = model.entities.filter((e) => e.kind === 'element' && (e.frameValues[ordering] ?? e.raw[ordering]) === value);
  const ids = new Set(elements.map((e) => e.id));
  const artifacts = model.entities.filter(
    (e) => e.kind === 'artifact' && model.connections.some((c) => c.kind === 'composition' && c.from === e.id && ids.has(c.to)),
  );
  return { artifacts: artifacts.length, elements: elements.length };
}

export function universeMap(scene: Scene, model: ExplorerModel, actions: MapActions, measure?: TextMeasurer): MapHandle {
  const root = document.createElement('div');
  root.className = 'world';
  const wires = document.createElementNS(SVG, 'svg');
  wires.classList.add('wires');
  wires.setAttribute('width', String(scene.bounds.x + scene.bounds.w + tokenNumber('--kb-scene-margin')));
  wires.setAttribute('height', String(scene.bounds.y + scene.bounds.h + tokenNumber('--kb-scene-margin')));
  root.append(wires);
  const labelsLayer = document.createElementNS(SVG, 'svg');
  labelsLayer.classList.add('labels-layer');
  labelsLayer.setAttribute('width', wires.getAttribute('width')!);
  labelsLayer.setAttribute('height', wires.getAttribute('height')!);
  const cards = new Map<string, HTMLElement>();
  const edges = new Map<string, SVGGElement>();
  const labels = new Map<string, SVGGElement>();
  const labelShapes = new Map<
    string,
    { text: string; anchor: Point; centre: Point; holder: SVGForeignObjectElement; leader: SVGPathElement }
  >();

  const named = byId(model);
  const marks = marksOf(model);
  const markOfBoundary = (id: string): Mark | null => {
    const concept = named.get(id);
    if (!concept) return null;
    return concept.kind === 'option'
      ? marks.value(concept.frameId ?? '', concept.sourceId, 'frame')
      : marks.frame(concept.sourceId, concept.kind);
  };

  for (const boundary of scene.layout.boundaries) {
    const section = document.createElement('section');
    section.className = 'boundary';
    section.dataset.role = boundary.role;
    section.dataset.id = boundary.id;
    section.style.left = `${boundary.x}px`;
    section.style.top = `${boundary.y}px`;
    section.style.width = `${boundary.w}px`;
    section.style.height = `${boundary.h}px`;
    if (boundary.title) {
      const heading = document.createElement('button');
      heading.type = 'button';
      heading.className = 'boundary-title';
      heading.dataset.part = 'heading';
      heading.dataset.boundary = boundary.id;
      const mark = markOfBoundary(boundary.id);
      if (mark) heading.append(markIcon(mark));
      const text = document.createElement('span');
      text.textContent = boundary.title;
      heading.append(text);
      heading.addEventListener('click', (event) => {
        event.stopPropagation();
        actions.selectEntity(boundary.id);
      });
      section.append(heading);
    }
    if (boundary.caption) {
      const caption = document.createElement('p');
      caption.className = 'boundary-caption';
      caption.dataset.part = 'heading';
      caption.textContent = boundary.caption;
      section.append(caption);
    }
    root.append(section);
  }

  for (const note of scene.layout.notes) {
    const said = document.createElement('p');
    said.className = 'boundary-note';
    said.dataset.boundary = note.scopeId;
    said.style.left = `${note.x}px`;
    said.style.top = `${note.y}px`;
    said.style.width = `${note.w}px`;
    said.style.height = `${note.h}px`;
    said.textContent = note.text;
    root.append(said);
  }

  for (const edge of scene.edges) {
    if (!edge.drawn) continue;
    const group = document.createElementNS(SVG, 'g');
    group.dataset.connection = edge.path;
    group.dataset.emphasis = 'rest';
    const hit = document.createElementNS(SVG, 'path');
    hit.setAttribute('d', edge.d);
    hit.classList.add('wire-hit');
    hit.setAttribute('role', 'button');
    hit.setAttribute('tabindex', '0');
    hit.setAttribute(
      'aria-label',
      `${human(edge.from.split(':').pop() ?? '')} to ${human(edge.to.split(':').pop() ?? '')}, ${edge.sources?.length ?? 1} connections`,
    );
    const wire = document.createElementNS(SVG, 'path');
    wire.setAttribute('d', edge.d);
    wire.classList.add('wire');
    wire.dataset.paint = edge.paint;
    wire.dataset.dash = edge.dash;
    group.append(hit, wire);
    if (edge.ordered && edge.points.length > 1) {
      const end = edge.points[edge.points.length - 1];
      const before = edge.points[edge.points.length - 2];
      const dx = Math.sign(end.x - before.x);
      const dy = Math.sign(end.y - before.y) || (dx ? 0 : 1);
      const size = tokenNumber('--kb-space-2');
      const tip = dy
        ? [end, { x: end.x - size / 2, y: end.y - dy * size }, { x: end.x + size / 2, y: end.y - dy * size }]
        : [end, { x: end.x - dx * size, y: end.y - size / 2 }, { x: end.x - dx * size, y: end.y + size / 2 }];
      const head = document.createElementNS(SVG, 'polygon');
      head.setAttribute('points', tip.map((p) => `${p.x},${p.y}`).join(' '));
      head.classList.add('arrowhead');
      head.dataset.paint = edge.paint;
      const holding = holdingDrawn(edge);
      if (holding) head.dataset.holding = holding;
      group.append(head);
    }
    const activate = (event: Event) => {
      event.stopPropagation();
      actions.selectConnection(edge.path);
    };
    hit.addEventListener('click', activate);
    hit.addEventListener('keydown', (event) => {
      if ((event as KeyboardEvent).key === 'Enter' || (event as KeyboardEvent).key === ' ') {
        event.preventDefault();
        activate(event);
      }
    });
    hit.addEventListener('pointerenter', () => actions.hover(edge.path));
    hit.addEventListener('pointerleave', () => actions.hover(''));
    wires.append(group);
    edges.set(edge.path, group);
  }

  const nameOf = (id: string): string => named.get(id)?.label ?? human(id.split(':').pop() ?? id);
  const endsOfEachEdge = new Map<string, string>();
  for (const edge of scene.edges)
    endsOfEachEdge.set(
      edge.path,
      edge.targetPair
        ? `${nameOf(edge.from)} · ${nameOf(edge.targetPair[0])} and ${nameOf(edge.targetPair[1])}`
        : `${nameOf(edge.from)} · ${nameOf(edge.to)}`,
    );

  for (const label of scene.labels) {
    const group = document.createElementNS(SVG, 'g');
    group.dataset.label = label.edge;
    const leader = document.createElementNS(SVG, 'path');
    leader.setAttribute('d', `M ${label.anchor.x} ${label.anchor.y} L ${label.box.x + label.box.w / 2} ${label.box.y + label.box.h / 2}`);
    leader.classList.add('leader');
    const holder = document.createElementNS(SVG, 'foreignObject');
    holder.setAttribute('x', String(label.box.x));
    holder.setAttribute('y', String(label.box.y));
    holder.setAttribute('width', String(label.box.w));
    holder.setAttribute('height', String(label.box.h));
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'label';
    button.dataset.part = 'label';
    button.textContent = label.text;
    button.setAttribute('aria-label', `${human(label.edge)}: ${label.text}`);
    button.title = endsOfEachEdge.get(label.edge) ?? '';
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      actions.selectConnection(label.edge);
    });
    button.addEventListener('pointerenter', () => actions.hover(label.edge));
    button.addEventListener('pointerleave', () => actions.hover(''));
    holder.append(button);
    group.append(leader, holder);
    labelsLayer.append(group);
    labels.set(label.edge, group);
    labelShapes.set(label.edge, {
      text: label.text,
      anchor: label.anchor,
      centre: { x: label.box.x + label.box.w / 2, y: label.box.y + label.box.h / 2 },
      holder,
      leader,
    });
  }

  const ownerRoles = roleOfTheBoundaryEachCardStandsIn(scene.layout);
  const clampedDescriptions: HTMLElement[] = [];
  for (const card of scene.layout.cards as PlacedCard[]) {
    const element =
      card.kind === 'option'
        ? optionCard(card, model, optionStats(model, card.id), actions.selectEntity)
        : entityCard(card, model, actions.selectEntity, measure);
    const ownerRole = ownerRoles.get(card.id);
    if (ownerRole) element.dataset.ownerRole = ownerRole;
    element.addEventListener('pointerenter', () => actions.hover(card.id));
    element.addEventListener('pointerleave', () => actions.hover(''));
    cards.set(card.id, element);
    if (DESCRIPTIONS_DRAWN_WITHIN_A_LINE_ALLOWANCE.includes(card.kind)) {
      const said = element.querySelector<HTMLElement>('.card-subtitle');
      if (said) clampedDescriptions.push(said);
    }
    root.append(element);
  }
  root.append(labelsLayer);

  const nubNodes = new Map<string, HTMLElement | SVGElement>();
  let nubTreatment = new Map<string, EdgeEmphasis>();

  function dressNub(node: HTMLElement | SVGElement, treatment: EdgeEmphasis) {
    node.dataset.emphasis = treatment;
    node.style.opacity = treatment === 'hidden' ? '0' : treatment === 'rest' ? String(tokenNumber('--kb-connection-opacity-idle')) : '1';
    node.style.pointerEvents = treatment === 'hidden' ? 'none' : '';
  }

  const countScale = (zoom: number) => grow(zoom, '--kb-count-zoom-growth');

  function setAttributeIfDifferent(node: Element, name: string, value: string) {
    if (node.getAttribute(name) !== value) node.setAttribute(name, value);
  }

  function paintLabelBoxes(zoom: number) {
    for (const shape of labelShapes.values()) {
      const box = labelBox(shape.text, shape.centre, zoom);
      setAttributeIfDifferent(shape.holder, 'x', String(box.x));
      setAttributeIfDifferent(shape.holder, 'y', String(box.y));
      setAttributeIfDifferent(shape.holder, 'width', String(box.w));
      setAttributeIfDifferent(shape.holder, 'height', String(box.h));
      setAttributeIfDifferent(shape.leader, 'd', `M ${shape.anchor.x} ${shape.anchor.y} L ${box.x + box.w / 2} ${box.y + box.h / 2}`);
    }
  }

  function replaceLabels(zoom: number) {
    for (const placed of labelLayer(scene.layout, scene.edges, scene.labelCandidates, zoom)) {
      const shape = labelShapes.get(placed.edge);
      if (!shape) continue;
      shape.anchor = placed.anchor;
      shape.centre = { x: placed.box.x + placed.box.w / 2, y: placed.box.y + placed.box.h / 2 };
    }
  }

  function paintNubs(placed: PlacedNub[], zoom: number) {
    for (const node of nubNodes.values()) node.remove();
    nubNodes.clear();
    for (const nub of placed) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'count';
      button.dataset.part = 'count';
      button.style.setProperty('--zoom-scale', String(countScale(zoom)));
      button.textContent = nub.count > MAX_DISPLAY_COUNT ? `${MAX_DISPLAY_COUNT}+` : String(nub.count);
      button.setAttribute('aria-label', `${human(nub.id.split(':').pop() ?? '')}: ${nub.count} connections`);
      button.addEventListener('click', (event) => {
        event.stopPropagation();
        actions.selectConnection(`nub:${nub.id}`);
      });
      const host = cards.get(nub.id);
      if (nub.inset && host) {
        button.classList.add('count-inset');
        host.append(button);
        button.dataset.nub = nub.id;
        nubNodes.set(nub.id, button);
      } else {
        const group = document.createElementNS(SVG, 'g');
        const line = document.createElementNS(SVG, 'path');
        line.setAttribute('d', `M ${nub.from.x} ${nub.from.y} L ${nub.box.x + nub.box.w / 2} ${nub.box.y + nub.box.h / 2}`);
        line.style.setProperty('--zoom-scale', String(countScale(zoom)));
        line.classList.add('nub-line');
        const holder = document.createElementNS(SVG, 'foreignObject');
        holder.setAttribute('x', String(nub.box.x));
        holder.setAttribute('y', String(nub.box.y));
        holder.setAttribute('width', String(nub.box.w));
        holder.setAttribute('height', String(nub.box.h));
        holder.append(button);
        group.append(line, holder);
        wires.append(group);
        group.dataset.nub = nub.id;
        nubNodes.set(nub.id, group);
      }
    }
    for (const [id, node] of nubNodes) dressNub(node, nubTreatment.get(id) ?? 'active');
  }

  let nubZoom = scene.zoom;
  paintNubs(scene.nubs, nubZoom);
  let labelGrowth = labelScale(scene.zoom);
  let describedAtHeadingScale = Number.NaN;

  function tellTheReaderWhateverIsClipped(headingScale: number) {
    let measured = false;
    for (const said of clampedDescriptions) {
      if (!said.clientHeight) continue;
      measured = true;
      if (said.scrollHeight > said.clientHeight) said.title = said.textContent ?? '';
      else said.removeAttribute('title');
    }
    if (measured) describedAtHeadingScale = headingScale;
  }

  function applyCamera(camera: Camera) {
    root.style.transform = `translate(${camera.x}px,${camera.y}px) scale(${camera.z})`;
    root.style.setProperty('--boundary-scale', String(boundaryScale(camera.z)));
    const headingScale = cardHeadingScale(camera.z);
    root.style.setProperty('--card-heading-scale', String(headingScale));
    root.dataset.headingGrown = String(headingScale !== 1);
    if (clampedDescriptions.length && headingScale !== describedAtHeadingScale) tellTheReaderWhateverIsClipped(headingScale);
    const scale = labelScale(camera.z);
    for (const group of labels.values())
      for (const node of group.querySelectorAll<HTMLElement | SVGElement>('button,.leader'))
        node.style.setProperty('--zoom-scale', String(scale));
    if (scene.labelCandidates.length && scale !== labelGrowth) {
      labelGrowth = scale;
      replaceLabels(camera.z);
    }
    paintLabelBoxes(camera.z);
    if (scene.nubs.length && camera.z !== nubZoom) {
      nubZoom = camera.z;
      paintNubs(nubLayer(scene.layout, scene.edges, nubZoom), nubZoom);
    }
  }

  function highlight(selection: Selection, hover: string) {
    const shown = emphasise(scene, selection, hover);
    const asState: Record<CardEmphasis, CardState> = { active: 'selected', idle: 'idle', hushed: 'hushed', dimmed: 'dimmed' };
    for (const [id, element] of cards) setCardState(element, asState[shown.cards.get(id) ?? 'idle'], id === shown.preview);
    for (const [path, group] of edges) {
      const edge = scene.edges.find((e) => e.path === path);
      if (!edge) continue;
      const treatment = shown.edges.get(path) ?? 'rest';
      const emphasisHold = edge.emphasized && treatment !== 'hidden' && !shown.settled;
      group.dataset.emphasis = treatment;
      group.style.opacity =
        treatment === 'active' || emphasisHold ? '1' : treatment === 'hidden' ? '0' : String(tokenNumber('--kb-connection-opacity-idle'));
      group.style.pointerEvents = treatment === 'hidden' ? 'none' : '';
      const wire = group.querySelector<SVGPathElement>('.wire');
      if (wire)
        wire.style.strokeWidth =
          treatment === 'active'
            ? String(tokenNumber('--kb-connection-stroke-selected'))
            : edge.emphasized
              ? String(tokenNumber('--kb-connection-stroke-preview'))
              : '';
    }
    nubTreatment = shown.nubs;
    for (const [id, node] of nubNodes) dressNub(node, shown.nubs.get(id) ?? 'active');
    for (const [path, group] of labels) {
      const treatment = shown.edges.get(path) ?? 'rest';
      group.style.opacity =
        treatment === 'hidden' ? '0' : treatment === 'active' ? '1' : String(tokenNumber('--kb-connection-opacity-label-faint'));
      group.style.pointerEvents = treatment === 'hidden' ? 'none' : '';
    }
  }

  function drawnBounds(): Rect {
    const origin = root.getBoundingClientRect();
    const scale = new DOMMatrixReadOnly(getComputedStyle(root).transform).a || 1;
    const boxes = [...root.querySelectorAll('.boundary,.boundary-title,.card')]
      .map((element) => element.getBoundingClientRect())
      .filter((box) => box.width && box.height);
    if (!boxes.length) return scene.bounds;
    const pad = tokenNumber('--kb-scene-margin');
    const x = Math.min(...boxes.map((b) => b.left - origin.left)) / scale - pad;
    const y = Math.min(...boxes.map((b) => b.top - origin.top)) / scale - pad;
    return {
      x,
      y,
      w: Math.max(...boxes.map((b) => b.right - origin.left)) / scale + pad - x,
      h: Math.max(...boxes.map((b) => b.bottom - origin.top)) / scale + pad - y,
    };
  }

  return { root, applyCamera, highlight, cardElement: (id) => cards.get(id), drawnBounds };
}
