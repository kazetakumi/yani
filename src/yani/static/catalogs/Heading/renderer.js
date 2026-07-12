// Heading — block-letter tag + highlighter-swiped section title.
export function render(props) {
  const h2 = document.createElement('h2');
  if (props.letter) {
    const tag = document.createElement('span');
    tag.className = 'block-letter';
    tag.textContent = props.letter;
    h2.appendChild(tag);
  }
  const hl = document.createElement('span');
  hl.className = 'hl';
  hl.textContent = props.text ?? '';
  h2.appendChild(hl);
  return h2;
}
