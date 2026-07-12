// EquationBlock — sage displayed equation, typeset by MathJax.
import { typeset } from '../../typeset.js';

export function render(props) {
  const el = document.createElement('div');
  el.className = 'equation-block';
  const label = document.createElement('div');
  label.className = 'equation-block-label';
  label.textContent = props.label ?? '';
  const tex = document.createElement('div');
  // TeX travels as text; MathJax's parser owns it (never innerHTML)
  tex.textContent = '\\[' + (props.tex ?? '') + '\\]';
  el.append(label, tex);
  if (props.tag) {
    const tag = document.createElement('span');
    tag.className = 'equation-tag';
    tag.textContent = props.tag;
    el.appendChild(tag);
  }
  if (props.caption) {
    const cap = document.createElement('div');
    cap.className = 'equation-caption';
    cap.textContent = props.caption;
    el.appendChild(cap);
  }
  typeset(el);
  return el;
}
