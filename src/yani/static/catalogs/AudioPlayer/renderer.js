export function render(props, ctx) {
  const el = document.createElement('figure');
  el.className = 'ui-audio';
  if (props.description !== undefined) {
    const caption = document.createElement('figcaption');
    caption.textContent = String(props.description);
    el.appendChild(caption);
  }
  const url = props.url === undefined ? undefined : ctx.safeUrl(props.url);
  if (!url) {
    const ph = document.createElement('div');
    ph.className = 'ui-media-placeholder pending';
    ph.textContent = props.url === undefined ? '…' : '[blocked audio URL]';
    el.appendChild(ph);
    return el;
  }
  const audio = document.createElement('audio');
  audio.controls = true;
  audio.src = url;
  el.appendChild(audio);
  return el;
}
