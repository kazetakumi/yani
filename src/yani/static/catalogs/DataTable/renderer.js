// DataTable — hand-ruled table; cells are plain text plus optional TeX.
import { typeset } from '../../typeset.js';

export function render(props) {
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const hr = document.createElement('tr');
  for (const h of props.headers ?? []) {
    const th = document.createElement('th');
    th.textContent = h;
    hr.appendChild(th);
  }
  thead.appendChild(hr);
  const tbody = document.createElement('tbody');
  for (const row of props.rows ?? []) {
    const tr = document.createElement('tr');
    for (const cell of row ?? []) {
      const td = document.createElement('td');
      td.textContent = cell;
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.append(thead, tbody);
  typeset(table);
  return table;
}
