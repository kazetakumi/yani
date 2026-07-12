export function render(props, ctx) {
  const wrap = document.createElement('label');
  wrap.className = 'ui-field';

  const label = document.createElement('span');
  label.className = 'ui-field-label';
  if (props.label !== undefined) label.textContent = String(props.label);

  const date = props.enableDate !== false; // date-only is the default
  const time = props.enableTime === true;

  const input = document.createElement('input');
  input.type = date && time ? 'datetime-local' : time ? 'time' : 'date';
  input.className = 'ui-input';
  if (typeof props.min === 'string') input.min = props.min;
  if (typeof props.max === 'string') input.max = props.max;
  if (typeof props.value === 'string' && props.value !== '') input.value = props.value;

  const path = ctx.raw.value?.path;
  input.addEventListener('change', () => ctx.write(path, input.value)); // ISO 8601 from the native picker

  wrap.append(label, input);
  return wrap;
}
