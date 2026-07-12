export function render(props, ctx) {
  const wrap = document.createElement('label');
  wrap.className = 'ui-field ui-slider';

  const label = document.createElement('span');
  label.className = 'ui-field-label';
  if (props.label !== undefined) label.textContent = String(props.label);

  const min = typeof props.min === 'number' ? props.min : 0;
  const max = typeof props.max === 'number' ? props.max : 100;

  const input = document.createElement('input');
  input.type = 'range';
  input.min = String(min);
  input.max = String(max);
  if (Number.isInteger(props.steps) && props.steps > 0) {
    input.step = String((max - min) / props.steps);
  }
  input.value = String(typeof props.value === 'number' ? props.value : min);

  const readout = document.createElement('output');
  readout.textContent = input.value;

  const path = ctx.raw.value?.path;
  input.addEventListener('input', () => {
    readout.textContent = input.value;
    ctx.write(path, Number(input.value));
  });

  wrap.append(label, input, readout);
  return wrap;
}
