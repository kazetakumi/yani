export function render(props, ctx) {
  const url = props.url === undefined ? undefined : ctx.safeUrl(props.url);
  if (!url) {
    const el = document.createElement('div');
    el.className = 'ui-media-placeholder pending';
    el.textContent = props.url === undefined ? '…' : '[blocked video URL]';
    return el;
  }
  const el = document.createElement('video');
  el.className = 'ui-video';
  el.controls = true;
  el.src = url;
  const poster = ctx.safeUrl(props.posterUrl);
  if (poster) el.poster = poster;
  return el;
}
