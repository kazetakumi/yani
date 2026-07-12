// GraphBlock — amber live graph (Chart.js) with one parameter slider.
const FAMILIES = {
  exp_decay: (k) => (x) => Math.exp(-k * x),
  exp_growth: (k) => (x) => Math.exp(k * x),
  sine: (k) => (x) => Math.sin(k * x),
  linear: (k) => (x) => k * x,
  quadratic: (k) => (x) => k * x * x,
  logistic: (k, xMax) => (x) => 1 / (1 + Math.exp(-k * (x - xMax / 2))),
};

export function render(props) {
  const el = document.createElement('div');
  el.className = 'graph-block';

  const header = document.createElement('div');
  header.className = 'graph-header';
  const t = document.createElement('span');
  t.textContent = props.title ?? '';
  const hint = document.createElement('span');
  hint.textContent = 'drag ' + (props.param_label ?? 'k');
  header.append(t, hint);

  const wrap = document.createElement('div');
  wrap.className = 'graph-canvas-wrap';
  const canvas = document.createElement('canvas');
  wrap.appendChild(canvas);

  const controls = document.createElement('div');
  controls.className = 'graph-controls';
  const lbl = document.createElement('label');
  lbl.textContent = props.param_label ?? 'k';
  const slider = document.createElement('input');
  slider.type = 'range';
  slider.min = String(props.param_min ?? 0.1);
  slider.max = String(props.param_max ?? 3);
  slider.step = String(((props.param_max ?? 3) - (props.param_min ?? 0.1)) / 28 || 0.1);
  slider.value = String(props.param_default ?? 1);
  const val = document.createElement('span');
  val.className = 'val';
  val.textContent = Number(slider.value).toFixed(1);
  controls.append(lbl, slider, val);

  const cap = document.createElement('div');
  cap.className = 'graph-caption';
  cap.textContent = props.caption ?? '';

  el.append(header, wrap, controls, cap);

  if (!window.Chart) {
    wrap.textContent = '[graph unavailable: Chart.js not loaded]';
    return el;
  }

  const xMax = props.x_max || 3;
  const xs = Array.from({ length: 61 }, (_, i) => (i / 60) * xMax);
  const family = FAMILIES[props.family] ?? FAMILIES.exp_decay;
  const ys = (k) => xs.map(family(k, xMax));

  window.Chart.defaults.font.family = "'Neucha', cursive";
  window.Chart.defaults.font.size = 14;
  const chart = new window.Chart(canvas, {
    type: 'line',
    data: {
      labels: xs.map((x) => x.toFixed(1)),
      datasets: [{ data: ys(Number(slider.value)), borderColor: '#cbab3a', pointRadius: 0, tension: 0.3 }],
    },
    options: {
      animation: false,
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { maxTicksLimit: 7 } } },
    },
  });
  slider.addEventListener('input', () => {
    val.textContent = Number(slider.value).toFixed(1);
    chart.data.datasets[0].data = ys(Number(slider.value));
    chart.update();
  });
  return el;
}
