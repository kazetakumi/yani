/* ─────────────────────────────────────────────────────────────
   sketch.js — hand-drawn-style SVG primitives for mentor lessons.
   Wobbly paths, curves, arrows, labels. No dependencies.
   Figures inherit the lesson's fonts and colour tokens (mentor.css).
   Strokes default to currentColor — mentor.css gives .figure-body svg
   the ink colour, and recolouring a container restyles its figure.
   Wobble is seeded per figure, so a figure renders identically
   on every page load and in print.

   Usage:
     <div id="fig-3-1"></div>
     <script>
       const s = Sketch.figure('#fig-3-1', { width: 640, height: 360 });
       s.arrow(60, 300, 60, 40);                       // y axis
       s.arrow(60, 300, 600, 300);                     // x axis
       s.curve([[80,280],[220,140],[380,180],[560,60]]);
       s.rect(400, 200, 140, 80, { stroke: 'var(--fig-border)' });
       s.label(320, 330, 'time →');
     </script>
───────────────────────────────────────────────────────────── */
(function (global) {
  'use strict';

  /* Deterministic PRNG (mulberry32) seeded from a string. */
  function makeRng(seedStr) {
    let h = 1779033703;
    for (let i = 0; i < seedStr.length; i++) {
      h = Math.imul(h ^ seedStr.charCodeAt(i), 3432918353);
      h = (h << 13) | (h >>> 19);
    }
    let a = h >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  const SVG_NS = 'http://www.w3.org/2000/svg';

  function el(name, attrs) {
    const node = document.createElementNS(SVG_NS, name);
    for (const k in attrs) node.setAttribute(k, attrs[k]);
    return node;
  }

  class SketchFigure {
    constructor(container, opts = {}) {
      const host = typeof container === 'string'
        ? document.querySelector(container) : container;
      if (!host) throw new Error('sketch.js: container not found: ' + container);
      this.w = opts.width || 640;
      this.h = opts.height || 360;
      this.wobble = opts.wobble != null ? opts.wobble : 1.6;
      this.rng = makeRng(String(opts.seed || host.id || 'mentor'));
      this.svg = el('svg', {
        viewBox: `0 0 ${this.w} ${this.h}`,
        role: 'img',
        style: 'width:100%;height:auto;display:block;overflow:visible',
      });
      host.appendChild(this.svg);
    }

    /* jitter a point by ±wobble */
    _j(p, wobble) {
      const w = wobble != null ? wobble : this.wobble;
      return [p[0] + (this.rng() * 2 - 1) * w, p[1] + (this.rng() * 2 - 1) * w];
    }

    /* Build a wobbly path through the given points: subdivide each
       segment ~every 45px, jitter interior points, smooth with
       quadratic beziers through midpoints. Returns a `d` string. */
    _wobblyPath(points, opts = {}) {
      const pts = [];
      for (let i = 0; i < points.length - 1; i++) {
        const [x1, y1] = points[i], [x2, y2] = points[i + 1];
        const len = Math.hypot(x2 - x1, y2 - y1);
        const steps = Math.max(2, Math.round(len / 45));
        for (let s = 0; s < steps; s++) {
          const t = s / steps;
          const p = [x1 + (x2 - x1) * t, y1 + (y2 - y1) * t];
          pts.push(s === 0 && i === 0 ? p : this._j(p, opts.wobble));
        }
      }
      pts.push(points[points.length - 1]);
      let d = `M ${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
      for (let i = 1; i < pts.length - 1; i++) {
        const mx = (pts[i][0] + pts[i + 1][0]) / 2;
        const my = (pts[i][1] + pts[i + 1][1]) / 2;
        d += ` Q ${pts[i][0].toFixed(1)} ${pts[i][1].toFixed(1)} ${mx.toFixed(1)} ${my.toFixed(1)}`;
      }
      const last = pts[pts.length - 1];
      d += ` L ${last[0].toFixed(1)} ${last[1].toFixed(1)}`;
      return d;
    }

    _stroke(d, opts = {}) {
      const path = el('path', {
        d,
        fill: opts.fill || 'none',
        stroke: opts.stroke || 'currentColor',
        'stroke-width': opts.width || 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      });
      if (opts.dash) path.setAttribute('stroke-dasharray', opts.dash);
      this.svg.appendChild(path);
      return path;
    }

    line(x1, y1, x2, y2, opts = {}) {
      return this._stroke(this._wobblyPath([[x1, y1], [x2, y2]], opts), opts);
    }

    /* Smooth wobbly curve through points: [[x,y], [x,y], …] */
    curve(points, opts = {}) {
      return this._stroke(this._wobblyPath(points, opts), opts);
    }

    arrow(x1, y1, x2, y2, opts = {}) {
      const g = el('g', {});
      this.svg.appendChild(g);
      const shaft = this.line(x1, y1, x2, y2, opts);
      const a = Math.atan2(y2 - y1, x2 - x1);
      const size = opts.head || 11;
      for (const side of [-1, 1]) {
        const hx = x2 - size * Math.cos(a + side * 0.45);
        const hy = y2 - size * Math.sin(a + side * 0.45);
        g.appendChild(this.line(hx, hy, x2, y2, opts));
      }
      g.insertBefore(shaft, g.firstChild);
      return g;
    }

    rect(x, y, w, h, opts = {}) {
      const pts = [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]];
      return this._stroke(this._wobblyPath(pts, opts), opts);
    }

    /* Wobbly ellipse: sampled circle points fed through the wobbler. */
    ellipse(cx, cy, rx, ry, opts = {}) {
      const pts = [];
      const n = Math.max(12, Math.round((rx + ry) / 8));
      const start = this.rng() * Math.PI * 2;
      for (let i = 0; i <= n; i++) {
        const t = start + (i / n) * Math.PI * 2;
        pts.push([cx + rx * Math.cos(t), cy + ry * Math.sin(t)]);
      }
      return this._stroke(this._wobblyPath(pts, opts), opts);
    }

    circle(cx, cy, r, opts = {}) {
      return this.ellipse(cx, cy, r, r, opts);
    }

    /* Text in the lesson hand. anchor: start | middle | end */
    label(x, y, text, opts = {}) {
      const t = el('text', {
        x, y,
        fill: opts.color || 'var(--ink-2)',
        'font-size': opts.size || 17,
        'text-anchor': opts.anchor || 'middle',
      });
      if (opts.rotate) t.setAttribute('transform', `rotate(${opts.rotate} ${x} ${y})`);
      t.textContent = text;
      this.svg.appendChild(t);
      return t;
    }

    /* Convenience: x/y axes with arrowheads and optional labels.
       origin: [x, y] in figure coords; xLen/yLen extend right/up. */
    axes(origin, xLen, yLen, opts = {}) {
      const [ox, oy] = origin;
      this.arrow(ox, oy, ox + xLen, oy, opts);
      this.arrow(ox, oy, ox, oy - yLen, opts);
      if (opts.xLabel) this.label(ox + xLen, oy + 24, opts.xLabel, { anchor: 'end' });
      if (opts.yLabel) this.label(ox - 10, oy - yLen - 8, opts.yLabel, { anchor: 'start' });
    }

    /* Plot y = fn(x) over [x0, x1] mapped into a pixel box.
       box: { x, y, w, h, x0, x1, y0, y1 } (y0 bottom, y1 top). */
    plot(fn, box, opts = {}) {
      const n = opts.samples || 60;
      const pts = [];
      for (let i = 0; i <= n; i++) {
        const xv = box.x0 + (i / n) * (box.x1 - box.x0);
        const yv = fn(xv);
        const px = box.x + ((xv - box.x0) / (box.x1 - box.x0)) * box.w;
        const py = box.y + box.h - ((yv - box.y0) / (box.y1 - box.y0)) * box.h;
        pts.push([px, py]);
      }
      return this._stroke(this._wobblyPath(pts, { wobble: opts.wobble != null ? opts.wobble : 0.8 }), opts);
    }
  }

  global.Sketch = {
    figure: (container, opts) => new SketchFigure(container, opts),
  };
})(window);
