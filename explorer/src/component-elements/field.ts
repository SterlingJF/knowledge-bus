export function field(label: string, control: HTMLElement, glyph?: Node): HTMLElement {
  const wrapper = document.createElement('div');
  wrapper.className = 'field';
  const heading = document.createElement('div');
  heading.className = 'field-label';
  if (glyph) heading.append(glyph);
  const text = document.createElement('span');
  text.textContent = label;
  heading.append(text);
  wrapper.append(heading, control);
  return wrapper;
}

export function hint(text: string): HTMLElement {
  const p = document.createElement('p');
  p.className = 'hint';
  p.textContent = text;
  return p;
}

export function divider(): HTMLElement {
  const hr = document.createElement('hr');
  hr.className = 'divider';
  return hr;
}
