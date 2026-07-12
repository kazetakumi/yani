// Definition — warm-tan callout; variants: model (sage), break (red dashed).
import { renderMarkdownInto } from '../../markdown.js';

export function render(props) {
  const el = document.createElement('div');
  el.className = 'definition';
  if (props.variant === 'model') el.classList.add('model');
  if (props.variant === 'break') el.classList.add('break');
  const label = document.createElement('div');
  label.className = 'definition-label';
  label.textContent = props.label ?? '';
  el.appendChild(label);
  renderMarkdownInto(el, props.text ?? '');
  return el;
}
