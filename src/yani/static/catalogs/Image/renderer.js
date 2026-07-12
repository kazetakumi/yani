const FIT = { contain: 'contain', cover: 'cover', fill: 'fill', none: 'none', scaleDown: 'scale-down' };

export function render(props, ctx) {
  const url = props.url === undefined ? undefined : ctx.safeUrl(props.url);
  if (!url) {
    const el = document.createElement('div');
    el.className = 'ui-image-placeholder pending';
    el.textContent = props.url === undefined ? '…' : '[blocked image URL]';
    return el;
  }
  const el = document.createElement('img');
  el.className = `ui-image ${props.variant ?? 'mediumFeature'}`;
  el.src = url;
  el.alt = props.description === undefined ? '' : String(props.description);
  if (FIT[props.fit]) el.style.objectFit = FIT[props.fit];
  return el;
}
