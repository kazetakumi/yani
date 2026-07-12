// Clicking dispatches the action through ctx.dispatchAction — currently
// the return-leg stub (console + DOM event); nothing reaches the server
// until the action protocol leg is built.
export function render(props, ctx) {
  const el = document.createElement('button');
  el.type = 'button';
  const variant = ['default', 'primary', 'borderless'].includes(props.variant) ? props.variant : 'default';
  el.className = `ui-button ${variant}`;
  el.appendChild(ctx.renderChild(props.child));
  el.addEventListener('click', () => ctx.dispatchAction(props.action));
  return el;
}
