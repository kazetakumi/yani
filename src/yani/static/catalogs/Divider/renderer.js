export function render(props) {
  const el = document.createElement('div');
  el.className = `ui-divider ${props.axis === 'vertical' ? 'vertical' : 'horizontal'}`;
  el.setAttribute('role', 'separator');
  return el;
}
