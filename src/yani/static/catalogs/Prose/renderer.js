// Prose — bare lesson paragraphs; inline markdown via the house parser.
import { renderMarkdownInto } from '../../markdown.js';

export function render(props) {
  const el = document.createElement('div');
  el.className = 'lesson-prose';
  const paragraphs = Array.isArray(props.paragraphs) ? props.paragraphs : [];
  renderMarkdownInto(el, paragraphs.join('\n\n'));
  return el;
}
