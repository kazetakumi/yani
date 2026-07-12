// Uses the native <dialog> element: showModal() gives focus trapping,
// backdrop and Esc-to-close for free — no hand-rolled overlay.
export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = 'ui-modal';

  const trigger = ctx.renderChild(props.trigger);
  const dialog = document.createElement('dialog');
  dialog.className = 'ui-modal-dialog';

  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'ui-modal-close';
  close.setAttribute('aria-label', 'Close');
  close.textContent = '✕';
  close.addEventListener('click', () => dialog.close());

  dialog.append(close, ctx.renderChild(props.content));
  trigger.addEventListener('click', () => dialog.showModal());

  el.append(trigger, dialog);
  return el;
}
