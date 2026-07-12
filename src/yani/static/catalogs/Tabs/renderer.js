// Tab switching is client-local state — the server never hears about it.
// The active panel re-renders on click via ctx.renderChild.
export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = 'ui-tabs';
  const bar = document.createElement('div');
  bar.className = 'ui-tabs-bar';
  const panel = document.createElement('div');
  panel.className = 'ui-tabs-panel';

  const tabs = Array.isArray(props.tabs) ? props.tabs : [];
  const buttons = tabs.map((tab, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'ui-tab';
    b.textContent = typeof tab.title === 'string' ? tab.title : `Tab ${i + 1}`;
    b.addEventListener('click', () => select(i));
    bar.appendChild(b);
    return b;
  });

  function select(i) {
    buttons.forEach((b, j) => b.classList.toggle('active', i === j));
    panel.replaceChildren(ctx.renderChild(tabs[i].child));
  }

  if (tabs.length) select(0);
  el.append(bar, panel);
  return el;
}
