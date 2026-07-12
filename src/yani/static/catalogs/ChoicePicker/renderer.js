let group = 0; // unique radio-group name per rendered picker

export function render(props, ctx) {
  const el = document.createElement('fieldset');
  const chips = props.displayStyle === 'chips';
  el.className = `ui-choice ${chips ? 'chips' : 'checkbox'}`;

  const legend = document.createElement('legend');
  if (props.label !== undefined) legend.textContent = String(props.label);
  el.appendChild(legend);

  const exclusive = props.variant === 'mutuallyExclusive';
  const name = `ui-choice-${group++}`;
  const path = ctx.raw.value?.path;
  const selected = new Set(Array.isArray(props.value) ? props.value.map(String) : []);
  const options = Array.isArray(props.options) ? props.options : [];

  let filter;
  if (props.filterable) {
    filter = document.createElement('input');
    filter.className = 'ui-input ui-choice-filter';
    filter.placeholder = 'Filter…';
    el.appendChild(filter);
  }

  const rows = options.map((opt) => {
    const row = document.createElement('label');
    row.className = 'ui-choice-option';
    const input = document.createElement('input');
    input.type = exclusive ? 'radio' : 'checkbox';
    if (exclusive) input.name = name;
    input.value = String(opt.value);
    input.checked = selected.has(String(opt.value));
    input.addEventListener('change', () => {
      if (exclusive) {
        ctx.write(path, [input.value]);
      } else {
        input.checked ? selected.add(input.value) : selected.delete(input.value);
        ctx.write(path, [...selected]);
      }
    });
    const text = document.createElement('span');
    text.textContent = typeof opt.label === 'string' ? opt.label : String(opt.value);
    row.append(input, text);
    el.appendChild(row);
    return { row, text: text.textContent.toLowerCase() };
  });

  filter?.addEventListener('input', () => {
    const q = filter.value.trim().toLowerCase();
    rows.forEach(({ row, text }) => { row.hidden = q !== '' && !text.includes(q); });
  });

  return el;
}
