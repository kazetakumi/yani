// ChipRow — one-tap checkpoint chips (spec 0002). A checkpoint is answered
// once: the first tap disables the whole row and marks the chosen chip.
export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = 'chip-row';
  if (props.note) {
    const note = document.createElement('div');
    note.className = 'chip-row-note';
    note.textContent = props.note;
    el.appendChild(note);
  }
  const row = document.createElement('div');
  row.className = 'chip-row-chips';
  const buttons = [];
  for (const chip of props.chips ?? []) {
    const btn = document.createElement('button');
    btn.type = 'button';
    const variant = ['primary', 'chip', 'quiet'].includes(chip.variant) ? chip.variant : 'chip';
    btn.className = `checkpoint-chip ${variant}`;
    btn.textContent = chip.label ?? '';
    btn.addEventListener('click', () => {
      buttons.forEach((b) => { b.disabled = true; });
      btn.classList.add('chosen');
      ctx.dispatchAction({ event: {
        name: chip.action ?? 'unnamed',
        context: { value: chip.value ?? chip.label ?? '', label: chip.label ?? '' },
      } });
    });
    buttons.push(btn);
    row.appendChild(btn);
  }
  el.appendChild(row);
  return el;
}
