import { panel } from '../component-elements/panel';
import { disclosureList, RESULT_LIMIT } from '../component-elements/disclosure-list';
import { type ExplorerModel, human } from '../lib/model';

export function searchPanel(model: ExplorerModel, pick: (id: string) => void, close: () => void): HTMLElement {
  const surface = panel('search', 'Find an artifact or element', close);
  surface.title.textContent = 'Find an artifact or element';
  const input = document.createElement('input');
  input.type = 'search';
  input.setAttribute('aria-label', 'Search names, aliases or questions');
  input.placeholder = 'Search names, aliases or questions';
  const results = document.createElement('div');
  results.setAttribute('aria-live', 'polite');
  surface.body.append(input, results);

  const candidates = model.entities.filter((e) => e.kind === 'artifact' || e.kind === 'element');
  const render = () => {
    const query = input.value.trim().toLowerCase();
    const matches = candidates.filter((e) => `${e.label} ${e.description} ${JSON.stringify(e.raw)}`.toLowerCase().includes(query));
    results.replaceChildren();
    if (!matches.length) {
      const empty = document.createElement('p');
      empty.className = 'muted';
      empty.textContent = 'No matches';
      results.append(empty);
      return;
    }
    results.append(
      disclosureList(
        matches.map((entity) => {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'result';
          button.dataset.result = entity.id;
          const kind = document.createElement('span');
          kind.className = 'muted';
          kind.textContent = human(entity.kind);
          const label = document.createElement('strong');
          label.textContent = entity.label;
          const detail = document.createElement('span');
          detail.className = 'muted';
          detail.textContent = entity.description || String(entity.raw.enablement?.action ?? '');
          button.append(kind, label, detail);
          button.addEventListener('click', () => pick(entity.id));
          return button;
        }),
        RESULT_LIMIT,
      ),
    );
  };
  input.addEventListener('input', render);
  render();
  return surface.root;
}
