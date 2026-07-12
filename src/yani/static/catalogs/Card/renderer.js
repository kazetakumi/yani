// Card holds exactly one child (spec rule) — multiple elements get
// wrapped in a Column by the composer, not by this renderer.
export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = 'ui-card';
  el.appendChild(ctx.renderChild(props.child));
  return el;
}
