// Chat wiring only: composing, streaming, and message bubbles.
// Everything ui.* is the rendering engine's job (ui.js).

import { handleUiEvent } from './ui.js';
import { renderMarkdownInto } from './markdown.js';

const chatEl = document.getElementById('chat');
const formEl = document.getElementById('composer-form');
const inputEl = document.getElementById('msg');
const sendEl = document.getElementById('send');
const loginGateEl = document.getElementById('login-gate');
const loginFormEl = document.getElementById('login-form');
const loginNameEl = document.getElementById('login-name');
const loginErrorEl = document.getElementById('login-error');
const logoutBtnEl = document.getElementById('logout-btn');

function showLoginError(message) {
  loginErrorEl.textContent = message;
  loginErrorEl.hidden = false;
}

function clearPlaceholder() {
  const p = chatEl.querySelector('.placeholder');
  if (p) p.remove();
}

function render(role, content) {
  clearPlaceholder();
  const row = document.createElement('div');
  row.className = `row ${role}`;
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'user' ? 'U' : 'A';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  // assistant text is markdown (rendered through our DOM-building parser,
  // never innerHTML); user text stays exactly as typed
  if (role === 'assistant') renderMarkdownInto(bubble, content);
  else bubble.textContent = content;
  row.append(avatar, bubble);
  chatEl.appendChild(row);
  chatEl.scrollTop = chatEl.scrollHeight;
  return row;
}

function renderNotice(message) {
  clearPlaceholder();
  const el = document.createElement('div');
  el.className = 'system-notice';
  el.textContent = message;
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;
}

// Rehydrate from the server's state, don't start from []. Items interleave
// text and UI in original order — surfaces (lessons included) replay from
// the durable store, so a reload loses nothing.
function loadHistory() {
  fetch('/history')
    .then(r => r.json())
    .then(data => data.items.forEach(item => {
      if (item.kind === 'text') {
        render(item.role, item.content);
      } else if (item.kind === 'ui') {
        clearPlaceholder();
        item.events.forEach(e => handleUiEvent(e, chatEl));
      }
    }));
}

// Name-entry gate (multi-user-workspaces map, ticket 03): on page load,
// check whether this browser already carries an identity cookie. If so,
// skip straight to the app — the whole point of the long-lived cookie is
// that you don't retype your name on every reload. Otherwise show the gate
// and only load history once /login succeeds.
fetch('/whoami')
  .then(r => r.json())
  .then(({ user }) => {
    if (user) {
      logoutBtnEl.hidden = false;
      loadHistory();
    } else {
      loginGateEl.hidden = false;
      loginNameEl.focus();
    }
  })
  .catch(() => {
    // Can't tell whether a user's already logged in — surface the gate
    // anyway so the page isn't just blank, and say why Start may not work.
    loginGateEl.hidden = false;
    loginNameEl.focus();
    showLoginError("Can't reach the server — check your connection and reload the page.");
  });

loginFormEl.addEventListener('submit', (e) => {
  e.preventDefault();
  const name = loginNameEl.value.trim();
  if (!name) return;
  loginErrorEl.hidden = true;
  const submitEl = loginFormEl.querySelector('button');
  submitEl.disabled = true;
  fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
    .then(r => {
      if (!r.ok) throw new Error(`login failed: ${r.status}`);
      return r.json();
    })
    .then(() => {
      loginGateEl.hidden = true;
      logoutBtnEl.hidden = false;
      loadHistory();
    })
    .catch(() => {
      showLoginError("Couldn't reach the server — check your connection and try again.");
    })
    .finally(() => { submitEl.disabled = false; });
});

// Switching identity on a shared browser (multi-user-workspaces map,
// per-request cookie identity): the cookie is httpOnly, so JS can't just
// clear it itself — it takes a server round-trip to expire it. A full page
// reload afterward is the simplest way to reset all in-memory chat state
// (message list, composer) rather than manually unwinding it here.
logoutBtnEl.addEventListener('click', () => {
  fetch('/logout', { method: 'POST' }).finally(() => location.reload());
});

// Transient "what's happening" line while tools run — removed the moment
// real content (text or UI) arrives. Friendlier names for the UI tools.
const TOOL_LABELS = {
  create_surface: 'preparing a view…',
  update_components: 'composing the layout…',
  update_data: 'filling in the data…',
  teach_lesson: 'planning your lesson…',
  read_workspace: 'checking your progress…',
  write_learning_record: 'writing a learning record…',
  update_mission: 'saving your profile…',
  create_concept: 'setting up a new concept…',
  update_concept_about: 'updating concept notes…',
  tick_concept_progress: 'updating progress…',
  set_active_concept: 'switching concepts…',
  update_about: 'getting to know you…',
};
let statusEl = null;
function showStatus(text) {
  if (!statusEl) {
    statusEl = document.createElement('div');
    statusEl.className = 'status-indicator';
    chatEl.appendChild(statusEl);
  }
  statusEl.textContent = text;
  chatEl.scrollTop = chatEl.scrollHeight;
}
function clearStatus() {
  if (statusEl) { statusEl.remove(); statusEl = null; }
}

function handleEvent(event, bubbleEl, assistantRow) {
  if (event.type === 'text.delta') {
    clearStatus();
    // accumulate the raw text and re-render the whole bubble: a delta can
    // split mid-token (half a **bold**), and re-parsing heals it
    bubbleEl.dataset.raw = (bubbleEl.dataset.raw ?? '') + event.text;
    renderMarkdownInto(bubbleEl, bubbleEl.dataset.raw);
    chatEl.scrollTop = chatEl.scrollHeight;
  } else if (event.type === 'tool.start') {
    showStatus(TOOL_LABELS[event.name] ?? `running ${event.name}…`);
  } else if (event.type.startsWith('ui.')) {
    clearStatus();
    handleUiEvent(event, chatEl);
  } else if (event.type === 'error') {
    clearStatus();
    renderNotice(event.message);
  } else if (event.type === 'turn.done') {
    clearStatus();
    // A UI-only turn ends silently — drop the empty bubble that was
    // opened in anticipation of text.
    if (bubbleEl.textContent === '') assistantRow.remove();
  }
}

// One streamed turn, whatever started it (typed message or UI action):
// POST the payload, read SSE frames off the body, dispatch each event.
// EventSource can't be used here — it only supports GET.
function streamTurn(url, payload) {
  const assistantRow = render('assistant', '');
  const bubbleEl = assistantRow.querySelector('.bubble');
  sendEl.disabled = true;

  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
    .then((res) => {
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      function pump() {
        return reader.read().then(({ done, value }) => {
          if (done) return;

          buffer += decoder.decode(value, { stream: true });

          // SSE frames are separated by a blank line. The final piece
          // after splitting may be a partial frame — keep it buffered
          // until the next chunk completes it.
          const frames = buffer.split('\n\n');
          buffer = frames.pop();

          for (const frame of frames) {
            if (!frame.startsWith('data: ')) continue;
            handleEvent(JSON.parse(frame.slice('data: '.length)), bubbleEl, assistantRow);
          }

          return pump();
        });
      }

      return pump();
    })
    .finally(() => { sendEl.disabled = false; });
}

formEl.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  render('user', text);
  inputEl.value = '';
  streamTurn('/chat', { message: text });
});

// The action return leg: the rendering engine emits a2ui:action DOM
// events (bubbling); the network hop happens here, symmetrical with a
// typed message — same loop, same SSE reply, different entry door.
document.addEventListener('a2ui:action', (e) => {
  renderNotice(`action: ${e.detail.name}`);
  streamTurn('/action', e.detail);
});

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    formEl.requestSubmit();
  }
});
