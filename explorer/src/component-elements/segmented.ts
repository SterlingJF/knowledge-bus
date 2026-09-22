export interface SegmentChoice {
  value: string;
  label: string;
  content?: () => Node;
  description?: string;
  tooltip?: string;
}

export function segmented(
  label: string,
  choices: SegmentChoice[],
  value: string,
  onChange: (value: string) => void,
  className = 'segment',
): HTMLElement {
  const group = document.createElement('div');
  group.className = className;
  group.setAttribute('role', 'group');
  group.setAttribute('aria-label', label);
  for (const choice of choices) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.value = choice.value;
    button.setAttribute('aria-pressed', String(choice.value === value));
    if (choice.tooltip) button.title = choice.tooltip;
    if (choice.content) button.append(choice.content());
    const text = document.createElement('span');
    text.textContent = choice.label;
    button.append(text);
    if (choice.description) {
      button.setAttribute('aria-label', `${choice.label}: ${choice.description}`);
      const small = document.createElement('small');
      small.textContent = choice.description;
      text.append(small);
    }
    button.addEventListener('click', () => onChange(choice.value));
    group.append(button);
  }
  return group;
}
