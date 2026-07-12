// ExplainBack — teal explain-it-back box; sends the learner's words to Yani.
export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = 'practice-block';
  const label = document.createElement('div');
  label.className = 'practice-block-label';
  label.textContent = 'Explain it back';
  const p = document.createElement('p');
  p.textContent = props.prompt_text ?? '';
  const ta = document.createElement('textarea');
  ta.className = 'explain-textarea';
  ta.placeholder = props.placeholder ?? 'No jargon. What is it, really?';
  const btn = document.createElement('button');
  btn.className = 'mentor-btn teal';
  btn.textContent = 'Send to Yani';
  btn.addEventListener('click', () => {
    const text = ta.value.trim();
    if (!text) return;
    ctx.dispatchAction({ event: { name: 'explain_back', context: { prompt: props.prompt_text ?? '', text } } });
    btn.disabled = true;
    btn.textContent = 'Sent ✓';
  });
  el.append(label, p, ta, btn);
  return el;
}
