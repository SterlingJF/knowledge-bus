export const DETAIL_LIMIT = 3;
export const RESULT_LIMIT = 5;

export function disclosureList(items: HTMLElement[], limit = DETAIL_LIMIT): HTMLElement {
  const group = document.createElement('div');
  group.append(...items);
  if (items.length <= limit) return group;
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'show-all';
  const render = (expanded: boolean) => {
    items.slice(limit).forEach((item) => {
      item.hidden = !expanded;
    });
    toggle.textContent = expanded ? 'Show fewer' : `Show all ${items.length}`;
    toggle.setAttribute('aria-expanded', String(expanded));
  };
  toggle.addEventListener('click', (event) => {
    event.stopPropagation();
    render(toggle.getAttribute('aria-expanded') !== 'true');
  });
  group.append(toggle);
  render(false);
  return group;
}
