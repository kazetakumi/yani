export function render(props, ctx) {
  const wrap = document.createElement('label');
  wrap.className = 'ui-check';

  const input = document.createElement('input');
  input.type = 'checkbox';
  input.checked = props.value === true;

  const path = ctx.raw.value?.path;
  input.addEventListener('change', () => ctx.write(path, input.checked));

  const label = document.createElement('span');
  if (props.label !== undefined) label.textContent = String(props.label);

  wrap.append(input, label);
  return wrap;
}
