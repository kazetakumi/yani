// SummaryBlock — espresso blackboard note: mental model first, then points.
export function render(props) {
  const el = document.createElement('div');
  el.className = 'summary-block';
  const label = document.createElement('div');
  label.className = 'summary-block-label';
  label.textContent = 'Summary';
  const h3 = document.createElement('h3');
  h3.textContent = props.title ?? '';
  const mm = document.createElement('div');
  mm.className = 'mental-model-final';
  const mmLabel = document.createElement('span');
  mmLabel.className = 'mm-label';
  mmLabel.textContent = 'Mental model';
  mm.append(mmLabel, '“' + (props.mental_model ?? '') + '”');
  const ul = document.createElement('ul');
  (props.points ?? []).forEach((point, i) => {
    const li = document.createElement('li');
    const n = document.createElement('span');
    n.className = 'sum-n';
    n.textContent = (i + 1) + '.';
    const span = document.createElement('span');
    span.textContent = point;
    li.append(n, span);
    ul.appendChild(li);
  });
  el.append(label, h3, mm, ul);
  return el;
}
