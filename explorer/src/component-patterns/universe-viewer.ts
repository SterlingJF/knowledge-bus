import patternsCss from '@/styles/patterns.css';
import tokensCss from '@/styles/tokens.css';
import {
  type ExplorerModel,
  type Camera,
  type Selection,
  type View,
  type ViewOptions,
  type ViewerState,
  emptySelection,
  initialOptions,
  updateOptions,
  validateModel,
} from '../lib/model';
import { type Rect, type Point } from '../lib/geometry';
import { buildScene, legendRows, selectionBounds, subjectBounds, type Scene, type PathSampler } from '../lib/scene';
import { serializeSvg, type SvgExportOptions } from '../lib/export';
import { type TextMeasurer, approximateText } from '../lib/card';
import {
  clampZoom,
  constrainCamera,
  fitCameraWithin,
  frameCamera,
  interpolate,
  motionDuration,
  noInsets,
  zoomAround,
  type Insets,
} from '../lib/camera';
import { tokenNumber } from '../lib/tokens';
import { showAfterTheLastOfferRests } from '../lib/dwell';
import { universeMap, type MapHandle } from './universe-map';
import { detailOverlay } from './detail-overlay';
import { connectionOverlay } from './connection-overlay';
import { viewOptionsMenu, type OptionsMenu } from './view-options';
import { searchPanel } from './search-panel';
import { minimap, type Minimap } from './minimap';
import { universeOverview } from './universe-overview';
import { dock, legend, shareMenu, topBar, type Dock, type TopBar } from './chrome';

export interface ViewerOptions {
  initial?: Partial<ViewOptions>;
}

export interface ViewerHandle {
  getState(): Readonly<ViewerState>;
  setViewOptions(patch: Partial<ViewOptions>): void;
  select(subject: string | null): void;
  selectConnection(path: string | null): void;
  fit(): void;
  exportSvg(options?: SvgExportOptions): Promise<string>;
  destroy(): void;
}

const OPENING_ORIGIN = 30;
const VIEW_ORIGIN = 25;
const OPENING_ZOOM = 0.8;
const FRAMES_ZOOM = 0.85;
const CONTENT_ZOOM = 0.7;
const DRAG_THRESHOLD = 4;
const DISMISS_THRESHOLD = 5;
const WHEEL_ZOOM_RATE = 0.005;
const STEP_ZOOM = tokenNumber('--kb-zoom-step');
const SAMPLE_COUNT = 41;
const PERCENT = 100;

function measurer(): TextMeasurer {
  const context = document.createElement('canvas').getContext('2d');
  if (!context) return approximateText;
  const cache = new Map<string, number>();
  return (text, size) => {
    const key = `${size}|${text}`;
    const known = cache.get(key);
    if (known !== undefined) return known;
    context.font = `${size}px ${getComputedStyle(document.body).fontFamily || 'sans-serif'}`;
    const width = context.measureText(text).width;
    cache.set(key, width);
    return width;
  };
}

function browserSampler(container: SVGSVGElement): PathSampler {
  const SVG = 'http://www.w3.org/2000/svg';
  return (d, count) => {
    const path = document.createElementNS(SVG, 'path');
    path.setAttribute('d', d);
    container.append(path);
    const length = path.getTotalLength();
    const samples = Array.from({ length: count }, (_, i) => {
      const point = path.getPointAtLength((length * (i + 1)) / (count + 1));
      return { x: point.x, y: point.y };
    });
    const middle = path.getPointAtLength(length / 2);
    path.remove();
    return { samples, middle: { x: middle.x, y: middle.y } };
  };
}

export function mountUniverseViewer(host: HTMLElement, input: unknown, viewerOptions: ViewerOptions = {}): ViewerHandle {
  const model: ExplorerModel = validateModel(input);
  const controller = new AbortController();
  const signal = controller.signal;
  const shadow = host.shadowRoot ?? host.attachShadow({ mode: 'open' });
  shadow.replaceChildren();
  const style = document.createElement('style');
  style.textContent = tokensCss + patternsCss;
  const shell = document.createElement('div');
  shell.className = 'shell';
  shell.tabIndex = -1;
  shadow.append(style, shell);

  const measure = measurer();
  let options = updateOptions(initialOptions(viewerOptions.initial?.view), viewerOptions.initial ?? {});
  let selection = emptySelection();
  let camera: Camera = { x: 0, y: 0, z: 1 };
  let insets: Insets = noInsets();
  let destroyed = false;
  let animation = 0;
  let scene: Scene;
  let map: MapHandle | null = null;
  const mapBounds = () => map?.drawnBounds() ?? scene.bounds;
  const hovered = showAfterTheLastOfferRests('', tokenNumber('--kb-motion-dwell'), (id) => map?.highlight(selection, id));
  let detail: HTMLElement | null = null;
  let search: HTMLElement | null = null;
  let overview: { scrim: HTMLElement; root: HTMLElement } | null = null;
  let share: HTMLElement | null = null;
  let overviewMap: Minimap | null = null;
  let legendBox: HTMLElement | null = null;

  const reducedMotion = () => !!globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const viewportSize = () => ({ width: viewport.clientWidth, height: viewport.clientHeight });
  const narrow = () => viewport.clientWidth < tokenNumber('--kb-size-narrow-threshold');

  const bar: TopBar = topBar(model, {
    openOverview: () => toggleOverview(),
    setView: (view: View) => setViewOptions({ view }),
    toggleTheme: () => setViewOptions({ theme: effectiveTheme() === 'light' ? 'dark' : 'light' }),
    toggleShare: () => toggleShare(),
  });
  const menu: OptionsMenu = viewOptionsMenu(
    model,
    () => options,
    (patch) => setViewOptions(patch),
    () => resetViewOptions(),
  );
  bar.utilities.append(menu.trigger);
  const viewport = document.createElement('div');
  viewport.className = 'viewport';
  viewport.setAttribute('aria-label', 'Universe map');
  const bottom: Dock = dock({
    search: () => (search ? closeSearch() : openSearch()),
    toggleMinimap: () => (overviewMap ? closeMinimap() : openMinimap()),
    fit: () => fit(),
    zoomIn: () => stepZoom(STEP_ZOOM),
    zoomOut: () => stepZoom(1 / STEP_ZOOM),
    actualSize: () => stepZoom(1 / camera.z),
  });
  shell.append(bar.root, viewport, bottom.root, menu.panel);

  const effectiveTheme = (): 'light' | 'dark' => {
    if (options.theme !== 'auto') return options.theme;
    return globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };

  const chromeTop = () => bar.root.offsetHeight;
  const chromeBottom = () => bottom.root.offsetHeight + tokenNumber('--kb-space-4') * 2;

  function applyCamera(next: Camera) {
    camera = constrainCamera({ ...next, z: clampZoom(next.z) }, mapBounds(), viewportSize(), insets);
    map?.applyCamera(camera);
    bottom.setZoom(camera.z);
    overviewMap?.update(camera, viewportSize());
  }

  function stopMotion() {
    if (animation) cancelAnimationFrame(animation);
    animation = 0;
  }

  function animateTo(target: Camera) {
    stopMotion();
    const goal = constrainCamera({ ...target, z: clampZoom(target.z) }, mapBounds(), viewportSize(), insets);
    if (reducedMotion()) {
      applyCamera(goal);
      return;
    }
    const from = { ...camera };
    const started = performance.now();
    const duration = motionDuration();
    const step = (now: number) => {
      const fraction = Math.min(1, (now - started) / duration);
      applyCamera(interpolate(from, goal, fraction));
      animation = fraction < 1 ? requestAnimationFrame(step) : 0;
    };
    animation = requestAnimationFrame(step);
  }

  function rebuild(keepCamera = false) {
    const previous = { ...camera };
    const hadFocus = shadow.activeElement;
    const probe = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    probe.style.position = 'absolute';
    probe.style.opacity = '0';
    viewport.append(probe);
    scene = buildScene(model, options, selection, camera.z, browserSampler(probe));
    probe.remove();
    map = universeMap(
      scene,
      model,
      {
        selectEntity: (id) => select(id),
        selectConnection: (path) => selectConnection(path),
        hover: (id) => hovered.offer(id),
      },
      measure,
    );
    map.highlight(selection, hovered.shown());
    viewport.replaceChildren(map.root);
    if (!scene.layout.cards.length) {
      const empty = document.createElement('p');
      empty.className = 'empty';
      empty.textContent = 'No cards match the current view options.';
      viewport.append(empty);
    }
    shell.dataset.theme = options.theme === 'auto' ? '' : options.theme;
    bar.renderTabs(options.view);
    bar.syncTheme(effectiveTheme());
    menu.render();
    legendBox?.remove();
    legendBox = null;
    const rows = legendRows(scene);
    if (rows.length) {
      legendBox = legend(rows);
      shell.append(legendBox);
    }
    if (overviewMap) {
      const position = { left: overviewMap.root.style.left, top: overviewMap.root.style.top };
      overviewMap.root.remove();
      overviewMap = null;
      openMinimap(position.left ? position : undefined);
    }
    applyCamera(keepCamera ? previous : camera);
    if (hadFocus && !shadow.contains(shadow.activeElement)) shell.focus({ preventScroll: true });
  }

  const subjectExists = (id: string) =>
    scene.layout.cards.some((c) => c.id === id) || scene.layout.boundaries.some((b) => b.id === id) || model.rules.some((r) => r.id === id);

  function computeInsets(): Insets {
    if (!detail) return noInsets();
    const width = detail.offsetWidth + tokenNumber('--kb-overlay-clearance') * 2;
    const height = detail.offsetHeight + tokenNumber('--kb-overlay-clearance') * 2;
    return narrow()
      ? { left: 0, right: 0, top: chromeTop() + height, bottom: chromeBottom() }
      : { left: width, right: 0, top: chromeTop(), bottom: chromeBottom() };
  }

  function panelTopAlongside(subjectCentre: number, height: number): number {
    const clearance = tokenNumber('--kb-overlay-clearance');
    const first = viewport.offsetTop + clearance;
    const last = viewport.offsetTop + viewport.clientHeight - chromeBottom() - height;
    return Math.max(first, Math.min(Math.max(first, last), viewport.offsetTop + subjectCentre - height / 2));
  }

  function placeDetail(against: Camera = camera) {
    if (!detail) return;
    insets = computeInsets();
    const bounds = narrow() ? null : subjectBounds(scene, selection);
    const top = bounds
      ? panelTopAlongside((bounds.y + bounds.h / 2) * against.z + against.y, detail.offsetHeight)
      : viewport.offsetTop + tokenNumber('--kb-overlay-clearance');
    detail.style.top = `${top}px`;
  }

  function closeDetail() {
    detail?.remove();
    detail = null;
    insets = noInsets();
  }

  function openDetail(node: HTMLElement) {
    closeDetail();
    detail = node;
    shell.append(detail);
    placeDetail();
  }

  function frameSelection() {
    const bounds = selectionBounds(scene, selection);
    if (!bounds) return;
    const target = frameCamera(bounds, viewportSize(), insets);
    if (!target) return;
    const goal = constrainCamera({ ...target, z: clampZoom(target.z) }, mapBounds(), viewportSize(), insets);
    placeDetail(goal);
    animateTo(goal);
  }

  function clearSelection(refit = true) {
    selection = emptySelection();
    hovered.showNow('');
    closeDetail();
    closeShare();
    rebuild(true);
    if (refit) fit();
  }

  function dismissDetail() {
    if (!detail) return false;
    closeDetail();
    closeShare();
    fit();
    return true;
  }

  function select(subject: string | null) {
    if (destroyed) return;
    menu.close();
    closeShare();
    if (!subject) {
      clearSelection();
      return;
    }
    const entity = model.entities.find((e) => e.id === subject);
    if (entity && !subjectExists(subject)) {
      const view: View =
        entity.kind === 'element'
          ? 'elements'
          : entity.kind === 'artifact'
            ? options.view === 'frames'
              ? 'artifacts'
              : options.view
            : 'frames';
      options = updateOptions(options, { view, frames: [] });
      selection = emptySelection();
      rebuild();
    }
    if (!subjectExists(subject)) return;
    closeSearch();
    selection = { entity: subject, connection: '', option: subject.startsWith('option:') ? subject : '' };
    rebuild(true);
    openDetail(
      detailOverlay(
        model,
        subject,
        () => dismissDetail(),
        (id) => select(id),
      ).root,
    );
    frameSelection();
  }

  function selectConnection(path: string | null) {
    if (destroyed) return;
    menu.close();
    if (!path || selection.connection === path) {
      clearSelection();
      return;
    }
    const nub = path.startsWith('nub:');
    const id = nub ? path.slice(4) : '';
    const edge = nub
      ? {
          path,
          from: id,
          to: id,
          label: 'Connections',
          ordered: false,
          nub: true,
          sources: scene.edges
            .filter((e) => e.from === id || e.to === id || e.targetPair?.includes(id))
            .flatMap((e) => e.sources ?? [{ source: e, composition: [] }]),
        }
      : scene.edges.find((e) => e.path === path);
    if (!edge) return;
    selection = { entity: '', connection: path, option: '' };
    closeSearch();
    rebuild(true);
    openDetail(
      connectionOverlay(
        model,
        edge,
        () => dismissDetail(),
        (target) => select(target),
      ),
    );
    frameSelection();
  }

  function setViewOptions(patch: Partial<ViewOptions>) {
    if (destroyed) return;
    const next = updateOptions(options, patch);
    const viewChanged = next.view !== options.view;
    options = next;
    if (viewChanged) {
      selection = emptySelection();
      closeDetail();
      rebuild();
      applyCamera(openingCamera(options.view));
      return;
    }
    rebuild(true);
    if (selection.entity)
      openDetail(
        detailOverlay(
          model,
          selection.entity,
          () => dismissDetail(),
          (id) => select(id),
        ).root,
      );
    menu.render();
  }

  function resetViewOptions() {
    const saved = { ...camera };
    const keep = selection;
    options = updateOptions(initialOptions(options.view), { ...viewerOptions.initial, view: options.view });
    selection = keep;
    rebuild(true);
    applyCamera(saved);
    if (selection.entity)
      openDetail(
        detailOverlay(
          model,
          selection.entity,
          () => dismissDetail(),
          (id) => select(id),
        ).root,
      );
    menu.render();
  }

  function fit() {
    animateTo(fitCameraWithin(mapBounds(), viewportSize(), insets));
  }

  function openingCamera(view: View, first = false): Camera {
    const origin = first ? OPENING_ORIGIN : VIEW_ORIGIN;
    return { x: origin, y: origin, z: first ? OPENING_ZOOM : view === 'frames' ? FRAMES_ZOOM : CONTENT_ZOOM };
  }

  function stepZoom(factor: number) {
    animateTo(zoomAround(camera, camera.z * factor, viewport.clientWidth / 2, viewport.clientHeight / 2));
  }

  function openSearch() {
    menu.close();
    closeSearch();
    search = searchPanel(
      model,
      (id) => select(id),
      () => closeSearch(),
    );
    shell.append(search);
    search.style.top = `${viewport.offsetTop + tokenNumber('--kb-overlay-clearance')}px`;
    search.querySelector('input')?.focus();
  }
  function closeSearch() {
    search?.remove();
    search = null;
  }

  function openMinimap(position?: { left: string; top: string }) {
    overviewMap = minimap(
      scene,
      (delta) => applyCamera({ ...camera, x: camera.x - delta.x * camera.z, y: camera.y - delta.y * camera.z }),
      (point) =>
        applyCamera({ ...camera, x: viewport.clientWidth / 2 - point.x * camera.z, y: viewport.clientHeight / 2 - point.y * camera.z }),
      () => closeMinimap(),
    );
    if (position) Object.assign(overviewMap.root.style, position, { right: 'auto', bottom: 'auto' });
    shell.append(overviewMap.root);
    overviewMap.update(camera, viewportSize());
    bottom.setMinimapOpen(true);
  }
  function closeMinimap() {
    overviewMap?.root.remove();
    overviewMap = null;
    bottom.setMinimapOpen(false);
  }

  function toggleOverview() {
    if (overview) {
      overview.scrim.remove();
      overview.root.remove();
      overview = null;
      return;
    }
    overview = universeOverview(model, () => toggleOverview());
    shell.append(overview.scrim, overview.root);
  }

  function toggleShare() {
    if (share) {
      closeShare();
      return;
    }
    share = shareMenu(() => void download());
    bar.utilities.append(share);
    bar.shareButton.setAttribute('aria-expanded', 'true');
  }
  function closeShare() {
    share?.remove();
    share = null;
    bar.shareButton.setAttribute('aria-expanded', 'false');
  }

  async function exportSvg(exportOptions: SvgExportOptions = {}): Promise<string> {
    await document.fonts?.ready;
    const probe = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    probe.style.position = 'absolute';
    probe.style.opacity = '0';
    viewport.append(probe);
    const clean = buildScene(model, options, emptySelection(), 1, browserSampler(probe));
    probe.remove();
    return serializeSvg(clean, model, exportOptions.theme ?? 'auto', measure);
  }

  async function download() {
    const svg = await exportSvg();
    const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${model.universe.id}-map.svg`;
    anchor.click();
    URL.revokeObjectURL(url);
    closeShare();
  }

  const pointers = new Map<number, Point>();
  let press: { x: number; y: number; moved: boolean; camera: Camera } | null = null;
  let pinch: { distance: number; camera: Camera } | null = null;
  const local = (event: PointerEvent): Point => {
    const box = viewport.getBoundingClientRect();
    return { x: event.clientX - box.left, y: event.clientY - box.top };
  };
  viewport.addEventListener(
    'pointerdown',
    (event) => {
      if ((event.target as Element).closest('button,[role=button],.panel')) return;
      stopMotion();
      viewport.setPointerCapture(event.pointerId);
      pointers.set(event.pointerId, local(event));
      if (pointers.size === 2) {
        const [a, b] = [...pointers.values()];
        pinch = { distance: Math.hypot(a.x - b.x, a.y - b.y), camera: { ...camera } };
        press = null;
      } else {
        const point = local(event);
        press = { x: point.x, y: point.y, moved: false, camera: { ...camera } };
      }
    },
    { signal },
  );
  viewport.addEventListener(
    'pointermove',
    (event) => {
      if (!pointers.has(event.pointerId)) return;
      pointers.set(event.pointerId, local(event));
      if (pinch && pointers.size === 2) {
        const [a, b] = [...pointers.values()];
        const distance = Math.hypot(a.x - b.x, a.y - b.y);
        applyCamera(zoomAround(pinch.camera, (pinch.camera.z * distance) / pinch.distance, (a.x + b.x) / 2, (a.y + b.y) / 2));
        return;
      }
      if (!press) return;
      const point = local(event);
      const dx = point.x - press.x;
      const dy = point.y - press.y;
      if (!press.moved && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
      press.moved = true;
      applyCamera({ z: press.camera.z, x: press.camera.x + dx, y: press.camera.y + dy });
    },
    { signal },
  );
  const release = (event: PointerEvent) => {
    pointers.delete(event.pointerId);
    if (pointers.size < 2) pinch = null;
    if (!press) return;
    const point = local(event);
    const still = Math.hypot(point.x - press.x, point.y - press.y) < DISMISS_THRESHOLD;
    const blank = !(event.target as Element).closest('button,[role=button],.panel');
    if (still && blank && event.type === 'pointerup' && (selection.entity || selection.connection)) clearSelection();
    press = null;
  };
  viewport.addEventListener('pointerup', release, { signal });
  viewport.addEventListener('pointercancel', release, { signal });
  viewport.addEventListener(
    'dblclick',
    (event) => {
      if ((event.target as Element).closest('button,[role=button],.panel')) return;
      event.preventDefault();
      fit();
    },
    { signal },
  );
  viewport.addEventListener(
    'wheel',
    (event) => {
      if ((event.target as Element).closest('.panel')) return;
      event.preventDefault();
      stopMotion();
      const box = viewport.getBoundingClientRect();
      if (event.ctrlKey || event.metaKey)
        applyCamera(
          zoomAround(camera, camera.z * Math.exp(-event.deltaY * WHEEL_ZOOM_RATE), event.clientX - box.left, event.clientY - box.top),
        );
      else applyCamera({ ...camera, x: camera.x - event.deltaX, y: camera.y - event.deltaY });
    },
    { passive: false, signal },
  );
  shell.addEventListener(
    'pointerdown',
    (event) => {
      const target = event.target as Node;
      if (menu.isOpen() && !menu.panel.contains(target) && !menu.trigger.contains(target)) menu.close();
      if (share && !share.contains(target) && !bar.shareButton.contains(target)) closeShare();
    },
    { capture: true, signal },
  );
  shell.addEventListener(
    'keydown',
    (event) => {
      if (event.key !== 'Escape') return;
      if (menu.isOpen()) menu.close(true);
      else if (share) closeShare();
      else if (overview) toggleOverview();
      else if (search) closeSearch();
      else if (!dismissDetail()) return;
      else return;
      event.preventDefault();
    },
    { signal },
  );

  const resize = new ResizeObserver(() => {
    if (destroyed) return;
    placeDetail();
    applyCamera(camera);
    overviewMap?.keepWithin();
  });
  resize.observe(viewport);

  const scheme = globalThis.matchMedia?.('(prefers-color-scheme: dark)');
  scheme?.addEventListener('change', () => bar.syncTheme(effectiveTheme()), { signal });

  scene = buildScene(model, options, selection, 1);
  rebuild();
  applyCamera(openingCamera(options.view, true));
  document.fonts?.ready.then(() => {
    if (destroyed) return;
    rebuild(true);
    if (selection.entity || selection.connection) frameSelection();
    else applyCamera(camera);
  });

  return {
    getState: () => ({
      options: { ...options, emphasis: [...options.emphasis], frames: [...options.frames] },
      selection: { ...selection },
      camera: { ...camera },
    }),
    setViewOptions,
    select,
    selectConnection,
    fit,
    exportSvg,
    destroy() {
      if (destroyed) return;
      destroyed = true;
      stopMotion();
      hovered.showNow('');
      controller.abort();
      resize.disconnect();
      shadow.replaceChildren();
    },
  };
}
