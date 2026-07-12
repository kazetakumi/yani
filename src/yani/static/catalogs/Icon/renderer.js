// System icon names mapped to text glyphs — no icon font, no external
// assets (keeps the client dependency-free). Unknown names render as a
// visible chip, never silently.
const GLYPHS = {
  accountCircle: '👤', add: '＋', arrowBack: '←', arrowForward: '→', attachFile: '📎',
  calendarToday: '📅', call: '📞', camera: '📷', check: '✓', close: '✕',
  delete: '🗑', download: '⬇', edit: '✏️', event: '📆', error: '❗',
  fastForward: '⏩', favorite: '❤️', favoriteOff: '🤍', folder: '📁', help: '❓',
  home: '🏠', info: 'ℹ️', locationOn: '📍', lock: '🔒', lockOpen: '🔓',
  mail: '✉️', menu: '☰', moreVert: '⋮', moreHoriz: '⋯', notificationsOff: '🔕',
  notifications: '🔔', pause: '⏸', payment: '💳', person: '👤', phone: '📱',
  photo: '🖼', play: '▶', print: '🖨', refresh: '↻', rewind: '⏪',
  search: '🔍', send: '➤', settings: '⚙️', share: '📤', shoppingCart: '🛒',
  skipNext: '⏭', skipPrevious: '⏮', star: '★', starHalf: '✬', starOff: '☆',
  stop: '⏹', upload: '⬆', visibility: '👁', visibilityOff: '🚫',
  volumeDown: '🔉', volumeMute: '🔇', volumeOff: '🔈', volumeUp: '🔊', warning: '⚠️',
};

export function render(props) {
  const el = document.createElement('span');
  const glyph = GLYPHS[props.name];
  if (glyph) {
    el.className = 'ui-icon';
    el.textContent = glyph;
    el.setAttribute('role', 'img');
    el.setAttribute('aria-label', String(props.name));
  } else {
    el.className = 'ui-icon unknown';
    el.textContent = props.name === undefined ? '…' : `[${String(props.name)}]`;
  }
  return el;
}
