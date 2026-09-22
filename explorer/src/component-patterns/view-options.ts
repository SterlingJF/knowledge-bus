import { icon, markIcon } from '../component-elements/icon';
import { iconButton, labelledButton } from '../component-elements/icon-button';
import { segmented } from '../component-elements/segmented';
import { chip } from '../component-elements/chip';
import { field, hint, divider } from '../component-elements/field';
import { type ExplorerModel, type ViewOptions, aViewGroupsItsElements, human, relationKinds } from '../lib/model';
import { relationKindCopy } from '../lib/phrasing';
import { marksOf } from '../lib/icons';

type Page = 'root' | 'frames' | 'emphasis';

export interface OptionsMenu {
  trigger: HTMLButtonElement;
  panel: HTMLElement;
  render(): void;
  open(): void;
  close(focusTrigger?: boolean): void;
  isOpen(): boolean;
}

function connectorSample(counted: boolean): HTMLElement {
  const sample = document.createElement('span');
  sample.className = 'sample';
  sample.setAttribute('aria-hidden', 'true');
  const start = document.createElement('span');
  start.className = 'sample-endpoint';
  const line = document.createElement('span');
  line.className = 'sample-connector';
  sample.append(start, line);
  const end = document.createElement('span');
  if (counted) {
    end.className = 'sample-badge';
    end.textContent = '3';
  } else end.className = 'sample-endpoint';
  sample.append(end);
  return sample;
}

function strokeSample(dashed: boolean): HTMLElement {
  const sample = document.createElement('span');
  sample.className = 'stroke-sample';
  sample.dataset.dashed = String(dashed);
  sample.setAttribute('aria-hidden', 'true');
  return sample;
}

function strokeStack(): HTMLElement {
  const stack = document.createElement('span');
  stack.className = 'stroke-stack';
  stack.setAttribute('aria-hidden', 'true');
  stack.append(strokeSample(false), strokeSample(true));
  return stack;
}

export function viewOptionsMenu(
  model: ExplorerModel,
  current: () => ViewOptions,
  apply: (patch: Partial<ViewOptions>) => void,
  reset: () => void,
): OptionsMenu {
  let page: Page = 'root';
  const marks = marksOf(model);
  const panel = document.createElement('section');
  panel.className = 'panel settings';
  panel.id = 'explorer-view-options';
  panel.setAttribute('aria-label', 'View options');
  panel.hidden = true;
  const trigger = iconButton('menu', 'View options', () => (panel.hidden ? open() : close()));
  trigger.classList.add('menu-trigger');
  trigger.setAttribute('aria-expanded', 'false');
  trigger.setAttribute('aria-controls', panel.id);
  const dot = document.createElement('span');
  dot.className = 'active-dot';
  dot.hidden = true;
  trigger.append(dot);

  const orderingFrame = model.entities.find((e) => e.id === model.orderingFrameId);
  const orderingOptions = model.entities.filter(
    (e) => e.kind === 'option' && !!orderingFrame && e.id.startsWith(`option:${orderingFrame.sourceId}:`),
  );
  const otherFrames = model.entities.filter((e) => (e.kind === 'frame' || e.kind === 'factor') && e.id !== model.orderingFrameId);
  const kinds = relationKinds(model);

  const toggleIn = (key: 'frames' | 'emphasis', value: string) => {
    const set = new Set(current()[key]);
    if (set.has(value)) set.delete(value);
    else set.add(value);
    apply({ [key]: [...set] } as Partial<ViewOptions>);
  };

  const chips = (items: HTMLElement[]) => {
    const group = document.createElement('div');
    group.className = 'chips';
    group.append(...items);
    return group;
  };

  const heading = (title: string, action?: HTMLElement) => {
    const head = document.createElement('div');
    head.className = 'settings-head';
    if (page !== 'root') {
      const back = iconButton('back', 'Back to view options', () => {
        const origin = page;
        page = 'root';
        render();
        panel.querySelector<HTMLElement>(`[data-page="${origin}"]`)?.focus();
      });
      back.classList.add('back');
      head.append(back);
    }
    const strong = document.createElement('strong');
    strong.textContent = title;
    head.append(strong);
    if (action) head.append(action);
    return head;
  };

  const clearAction = (label: string, enabled: boolean, action: () => void) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'muted';
    button.textContent = label;
    button.disabled = !enabled;
    button.addEventListener('click', action);
    return button;
  };

  const pageRow = (label: string, detail: string, target: Page, glyph?: string) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'disclosure';
    button.dataset.page = target;
    if (glyph) button.append(icon(glyph));
    const text = document.createElement('span');
    text.textContent = label;
    const small = document.createElement('small');
    small.textContent = detail;
    button.append(text, small, icon('chevron'));
    button.addEventListener('click', () => {
      page = target;
      render();
      panel.querySelector<HTMLElement>('.back')?.focus();
    });
    return button;
  };

  function render() {
    const options = current();
    dot.hidden = !(options.frames.length || options.emphasis.length);
    panel.replaceChildren();
    if (page === 'frames') {
      panel.append(
        heading(
          'Dimensions',
          clearAction('Clear', options.frames.length > 0, () => apply({ frames: [] })),
        ),
      );
      if (orderingFrame)
        panel.append(
          field(
            orderingFrame.label,
            chips(
              orderingOptions.map((option) =>
                chip(option.id, option.label, options.frames.includes(option.id), marks.value(orderingFrame.id, option.sourceId), () =>
                  toggleIn('frames', option.id),
                ),
              ),
            ),
            markIcon(marks.frame(orderingFrame.sourceId)),
          ),
        );
      const frames = otherFrames.filter((e) => e.kind === 'frame');
      const factors = otherFrames.filter((e) => e.kind === 'factor');
      for (const [label, items] of [
        ['Referenced frames', frames],
        ['Referenced factors', factors],
      ] as const)
        if (items.length)
          panel.append(
            field(
              label,
              chips(
                items.map((frame) =>
                  chip(frame.id, frame.label, options.frames.includes(frame.id), marks.frame(frame.sourceId, frame.kind), () =>
                    toggleIn('frames', frame.id),
                  ),
                ),
              ),
            ),
          );
      panel.append(hint('Any selected value in each group.'));
      return;
    }
    if (page === 'emphasis') {
      panel.append(
        heading(
          'Emphasize connections',
          clearAction('Reset emphasis', options.emphasis.length > 0, () => apply({ emphasis: [] })),
        ),
        hint('Choose one or more types. Other connections stay visible.'),
        chips(
          kinds.map((kind) => {
            const count = model.connections.filter((c) => c.kind === kind.id).length;
            return chip(kind.id, `${relationKindCopy(kind.id, kinds)} (${count})`, options.emphasis.includes(kind.id), null, () =>
              toggleIn('emphasis', kind.id),
            );
          }),
        ),
      );
      return;
    }
    panel.append(heading('View options'));
    if (aViewGroupsItsElements(options.view))
      panel.append(
        field(
          'Group elements',
          segmented(
            'Group elements',
            [
              { value: 'grouped', label: orderingFrame?.label ?? 'Ordering' },
              { value: 'none', label: 'None' },
            ],
            options.group ? 'grouped' : 'none',
            (value) => apply({ group: value === 'grouped' }),
          ),
        ),
      );
    if (options.view === 'frames') panel.append(hint('Frame choices and connections apply to the artifact views.'));
    else {
      panel.append(
        pageRow('Dimensions', options.frames.length ? `${options.frames.length} selected` : 'All cards', 'frames', 'filter'),
        divider(),
        field(
          'Connections',
          segmented(
            'Connections',
            [
              { value: '', label: 'Off' },
              { value: 'relations', label: 'Relations' },
              { value: 'composition', label: 'Composition' },
            ],
            options.connections,
            (value) => apply({ connections: value as ViewOptions['connections'] }),
          ),
        ),
      );
      if (options.connections === 'relations')
        panel.append(pageRow('Emphasize', options.emphasis.length ? `${options.emphasis.length} selected` : 'No emphasis', 'emphasis'));
      if (options.connections)
        panel.append(
          field(
            'Display',
            segmented(
              'Display',
              [
                { value: 'lines', label: 'Lines', content: () => connectorSample(false) },
                { value: 'counts', label: 'Counts', content: () => connectorSample(true) },
              ],
              options.display,
              (value) => apply({ display: value as ViewOptions['display'] }),
            ),
          ),
        );
      if (options.connections === 'composition' && options.display === 'lines')
        panel.append(
          field(
            'Composition lines',
            segmented(
              'Composition lines',
              [
                {
                  value: 'uniform',
                  label: 'Required',
                  tooltip: 'Hide situational connections',
                  content: () => strokeSample(false),
                },
                {
                  value: 'distinct',
                  label: 'Required / optional',
                  tooltip: 'Show all connections',
                  content: () => strokeStack(),
                },
              ],
              options.lineStyle,
              (value) => apply({ lineStyle: value as ViewOptions['lineStyle'] }),
            ),
          ),
        );
    }
    const resetRow = labelledButton('reset', 'Reset view options', reset);
    resetRow.classList.add('disclosure');
    resetRow.dataset.action = 'reset';
    panel.append(divider(), resetRow);
  }

  function open() {
    page = 'root';
    render();
    panel.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
  }
  function close(focusTrigger = false) {
    panel.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    if (focusTrigger) trigger.focus();
  }
  panel.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    event.stopPropagation();
    if (page !== 'root') {
      const origin = page;
      page = 'root';
      render();
      panel.querySelector<HTMLElement>(`[data-page="${origin}"]`)?.focus();
    } else close(true);
  });

  return { trigger, panel, render, open, close, isOpen: () => !panel.hidden };
}
