// PromptInput — free-text checkpoint (guess / try-one) with a one-tap
// escape. The escape must cost nothing: a guess is a gift, never a toll.
export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = 'prompt-input practice-block';
  const p = document.createElement('p');
  p.className = 'prompt-input-text';
  p.textContent = props.prompt_text ?? '';
  const ta = document.createElement('textarea');
  ta.className = 'explain-textarea';
  ta.placeholder = props.placeholder ?? '';
  const row = document.createElement('div');
  row.className = 'prompt-input-row';
  const send = document.createElement('button');
  send.className = 'mentor-btn teal';
  send.textContent = props.submit_label ?? 'Send';

  const finish = (button, doneLabel) => {
    send.disabled = true;
    ta.disabled = true;
    if (skipBtn) skipBtn.disabled = true;
    if (button) { button.textContent = doneLabel; }
  };

  send.addEventListener('click', () => {
    const text = ta.value.trim();
    if (!text) return;
    ctx.dispatchAction({ event: {
      name: props.action ?? 'unnamed',
      context: { prompt: props.prompt_text ?? '', text },
    } });
    finish(send, 'Sent ✓');
  });
  row.appendChild(send);

  let skipBtn = null;
  if (props.skip_label && props.skip_action) {
    skipBtn = document.createElement('button');
    skipBtn.type = 'button';
    skipBtn.className = 'checkpoint-chip quiet';
    skipBtn.textContent = props.skip_label;
    skipBtn.addEventListener('click', () => {
      ctx.dispatchAction({ event: {
        name: props.skip_action,
        context: { prompt: props.prompt_text ?? '' },
      } });
      finish(null, null);
    });
    row.appendChild(skipBtn);
  }

  el.append(p, ta, row);
  if (props.note) {
    const note = document.createElement('div');
    note.className = 'chip-row-note';
    note.textContent = props.note;
    el.appendChild(note);
  }
  return el;
}
