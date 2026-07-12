export function render(props, ctx) {
  const wrap = document.createElement('label');
  wrap.className = 'ui-field';

  const label = document.createElement('span');
  label.className = 'ui-field-label';
  if (props.label !== undefined) label.textContent = String(props.label);
  wrap.appendChild(label);

  const variant = props.variant ?? 'shortText';
  const input = variant === 'longText'
    ? document.createElement('textarea')
    : document.createElement('input');
  if (variant === 'number') input.type = 'number';
  if (variant === 'obscured') input.type = 'password';
  input.className = 'ui-input';
  if (props.placeholder !== undefined) input.placeholder = String(props.placeholder);
  if (props.value !== undefined) input.value = String(props.value);

  // two-way binding, client-local: write into the data model at the
  // path the value prop is bound to — no re-render, no server traffic
  const path = ctx.raw.value?.path;
  input.addEventListener('input', () => {
    ctx.write(path, variant === 'number' ? Number(input.value) : input.value);
  });

  wrap.appendChild(input);
  return wrap;
}
