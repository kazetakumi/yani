// TreeLocator — the "where you are" strip; plain styled text, no links (v1).
function row(key, value) {
  const r = document.createElement('div');
  r.className = 'tree-row';
  const k = document.createElement('span');
  k.className = 'tree-key';
  k.textContent = key;
  const v = document.createElement('span');
  v.className = 'tree-val';
  v.textContent = value;
  r.append(k, v);
  return r;
}

export function render(props) {
  const el = document.createElement('div');
  el.className = 'tree-locator';
  const label = document.createElement('div');
  label.className = 'tree-locator-label';
  label.textContent = 'Where you are';
  el.appendChild(label);
  el.appendChild(row('branches from', props.branches_from ?? ''));
  el.appendChild(row('unlocks next', props.unlocks_next ?? ''));
  if (props.primary_source) el.appendChild(row('primary source', props.primary_source));
  return el;
}
