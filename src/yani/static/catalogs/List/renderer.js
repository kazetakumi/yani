const ALIGN = { start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch' };

export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = `ui-list ${props.direction === 'horizontal' ? 'horizontal' : 'vertical'}`;
  if (ALIGN[props.align]) el.style.alignItems = ALIGN[props.align];
  for (const childId of props.children ?? []) {
    el.appendChild(ctx.renderChild(childId));
  }
  return el;
}
