// PracticeChecklist — teal local checklist; ticking is the learner's own tracker.
export function render(props) {
  const el = document.createElement('div');
  el.className = 'practice-block';
  const label = document.createElement('div');
  label.className = 'practice-block-label';
  label.textContent = props.label ?? 'Practice';
  const ul = document.createElement('ul');
  ul.className = 'practice-steps';
  for (const step of props.steps ?? []) {
    const li = document.createElement('li');
    li.className = 'practice-step';
    const box = document.createElement('input');
    box.type = 'checkbox';
    const span = document.createElement('span');
    span.textContent = step;
    box.addEventListener('change', () => li.classList.toggle('done', box.checked));
    li.append(box, span);
    ul.appendChild(li);
  }
  el.append(label, ul);
  return el;
}
