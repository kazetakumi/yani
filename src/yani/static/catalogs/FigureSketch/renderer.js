// FigureSketch — hand-drawn SVG figure from typed primitives (sketch.js).
export function render(props) {
  const fig = document.createElement('figure');
  fig.className = 'figure-block';
  const body = document.createElement('div');
  body.className = 'figure-body';
  const host = document.createElement('div');
  body.appendChild(host);
  const cap = document.createElement('figcaption');
  const strong = document.createElement('strong');
  strong.textContent = props.figure_label ?? '';
  cap.append(strong, ' — ' + (props.caption ?? ''));
  fig.append(body, cap);

  if (!window.Sketch) {
    host.textContent = '[figure unavailable: sketch.js not loaded]';
    return fig;
  }
  const s = window.Sketch.figure(host, { width: 640, height: 320, seed: props.figure_label || 'fig' });
  for (const e of props.elements ?? []) {
    try {
      if (e.kind === 'line') s.line(e.x1, e.y1, e.x2, e.y2);
      else if (e.kind === 'arrow') s.arrow(e.x1, e.y1, e.x2, e.y2);
      else if (e.kind === 'rect') s.rect(e.x, e.y, e.w, e.h, { stroke: 'var(--fig-border)' });
      else if (e.kind === 'circle') s.circle(e.cx, e.cy, e.r, { stroke: 'var(--fig-border)' });
      else if (e.kind === 'label') s.label(e.x, e.y, e.text);
      else if (e.kind === 'axes') s.axes([e.ox, e.oy], e.x_len, e.y_len, { xLabel: e.x_label ?? undefined, yLabel: e.y_label ?? undefined });
      else if (e.kind === 'curve' && Array.isArray(e.points) && e.points.length > 1) s.curve(e.points);
    } catch (err) {
      console.warn('FigureSketch element failed', e, err);
    }
  }
  return fig;
}
