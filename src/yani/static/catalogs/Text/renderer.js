// Renderer contract (same for every component):
//   render(props, ctx) -> HTMLElement
// props arrive with path bindings already resolved against the surface's
// data model — a binding with no value yet resolves to undefined.
// ctx: renderChild(id), raw (unresolved props), write(path, value),
//      dispatchAction(action), safeUrl(url).
// Model-supplied strings only ever meet textContent, never innerHTML.

export function render(props) {
  const el = document.createElement('p');
  el.className = 'ui-text';
  if (props.variant === 'caption') el.classList.add('caption');
  if (props.text === undefined) {
    el.classList.add('pending');
    el.textContent = '…';
  } else {
    el.textContent = String(props.text);
  }
  return el;
}
