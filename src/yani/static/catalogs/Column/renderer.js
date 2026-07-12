// Column is a container: it doesn't render children itself, it asks the
// engine to via ctx.renderChild(id) — the engine owns catalog lookup and
// cycle protection, so containers stay ignorant of other components.
const JUSTIFY = {
  start: 'flex-start', center: 'center', end: 'flex-end',
  spaceBetween: 'space-between', spaceAround: 'space-around',
  spaceEvenly: 'space-evenly', stretch: 'stretch',
};
const ALIGN = { start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch' };

export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = 'ui-column';
  if (JUSTIFY[props.justify]) el.style.justifyContent = JUSTIFY[props.justify];
  if (ALIGN[props.align]) el.style.alignItems = ALIGN[props.align];
  for (const childId of props.children ?? []) {
    el.appendChild(ctx.renderChild(childId));
  }
  return el;
}
