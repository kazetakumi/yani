// The rendering engine: owns the client-side surface store and turns
// ui.* events into DOM. Rendering is a pure function of stored state
// (components + data model): every event updates the store, then the
// whole surface re-renders from scratch. Deliberately simple — no
// diffing, no fine-grained bindings; a surface is small.

import { CATALOG } from './catalog.js';

// surface_id -> { el, components: [...] | null, data: {path: value} }
const surfaces = new Map();

const MAX_DEPTH = 32; // defense in depth: the server validates the tree, the client still refuses to hang on a bad one

function resolveProps(props, data) {
  const resolved = {};
  for (const [key, value] of Object.entries(props ?? {})) {
    if (value !== null && typeof value === 'object' && !Array.isArray(value)
        && Object.keys(value).length === 1 && typeof value.path === 'string') {
      resolved[key] = data[value.path]; // unfilled binding -> undefined, renderers show a pending state
    } else {
      resolved[key] = value;
    }
  }
  return resolved;
}

function errorChip(message) {
  const el = document.createElement('div');
  el.className = 'ui-error';
  el.textContent = message; // visible on purpose — a render problem should never be a silent no-op
  return el;
}

// Media/link URLs from the model are data, not trusted markup — same rule
// as textContent-only. The engine owns this boundary so no renderer can
// forget it (the spec's own openUrl guidance: scheme allowlist, anti-XSS).
function safeUrl(url) {
  try {
    const parsed = new URL(String(url), window.location.href);
    return (parsed.protocol === 'http:' || parsed.protocol === 'https:') ? parsed.href : null;
  } catch {
    return null;
  }
}

function renderComponent(id, byId, surface, seen, depth) {
  if (depth > MAX_DEPTH || seen.has(id)) return errorChip(`[cycle or depth limit at "${id}"]`);
  const node = byId.get(id);
  if (!node) return errorChip(`[unknown component id "${id}"]`);
  const renderFn = CATALOG[node.component];
  if (!renderFn) return errorChip(`[no renderer for "${node.component}"]`);

  seen.add(id);
  const ctx = {
    renderChild: (childId) => renderComponent(childId, byId, surface, seen, depth + 1),
    // raw, unresolved props — input renderers need the {"path": ...} object
    // itself (not its current value) to know where to write back.
    raw: node.props ?? {},
    // Two-way binding is client-local: writes land in the surface's data
    // model but deliberately do NOT re-render (a re-render per keystroke
    // would steal focus). The server only sees this data when an action
    // carries it — dispatchAction below, resolved at click time.
    write: (path, value) => { if (typeof path === 'string') surface.data[path] = value; },
    // The action return leg. Context bindings resolve against the data
    // model AT CLICK TIME — this is the moment locally-typed input
    // (TextField, CheckBox...) becomes visible to the server. The engine
    // only emits a DOM event; app.js owns the network call.
    dispatchAction: (action) => {
      const event = action?.event ?? {};
      const context = {};
      for (const [key, value] of Object.entries(event.context ?? {})) {
        context[key] = (value !== null && typeof value === 'object' && typeof value.path === 'string')
          ? surface.data[value.path]
          : value;
      }
      const detail = { surfaceId: surface.el.dataset.surfaceId, name: event.name ?? 'unnamed', context };
      surface.el.dispatchEvent(new CustomEvent('a2ui:action', { detail, bubbles: true }));
    },
    safeUrl,
  };
  const resolved = resolveProps(node.props, surface.data);
  const el = renderFn(resolved, ctx);
  if (typeof resolved.weight === 'number') el.style.flexGrow = String(resolved.weight); // spec-wide prop, applied centrally
  return el;
}

function renderSurface(surface) {
  surface.el.replaceChildren();
  if (!surface.components) {
    surface.el.classList.add('empty');
    return;
  }
  surface.el.classList.remove('empty');
  const byId = new Map(surface.components.map((c) => [c.id, c]));
  surface.el.appendChild(renderComponent('root', byId, surface, new Set(), 0));
}

function handleCreateSurface(event, chatEl) {
  const el = document.createElement('div');
  el.className = 'ui-surface empty';
  el.dataset.surfaceId = event.surface_id;
  chatEl.appendChild(el);
  surfaces.set(event.surface_id, { el, components: null, data: {} });
}

function handleUpdateComponents(event) {
  const surface = surfaces.get(event.surface_id);
  if (!surface) return console.error('updateComponents for unknown surface', event.surface_id);
  surface.components = event.components;
  renderSurface(surface);
}

function handleUpdateDataModel(event) {
  const surface = surfaces.get(event.surface_id);
  if (!surface) return console.error('updateDataModel for unknown surface', event.surface_id);
  Object.assign(surface.data, event.values);
  renderSurface(surface);
}

// The client-side twin of harness.py's _UI_TOOL_ACTIONS map.
const HANDLERS = {
  'ui.createSurface': handleCreateSurface,
  'ui.updateComponents': handleUpdateComponents,
  'ui.updateDataModel': handleUpdateDataModel,
};

export function handleUiEvent(event, chatEl) {
  const handler = HANDLERS[event.type];
  if (!handler) return console.error('unhandled ui event', event.type);
  handler(event, chatEl);
  chatEl.scrollTop = chatEl.scrollHeight;
}
