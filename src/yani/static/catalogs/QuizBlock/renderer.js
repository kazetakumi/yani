// QuizBlock — lavender retrieval question as a radio MCQ (the original
// mentor skill's quiz shape): pick an option, then "Check answer" reveals
// the verdict + explanation and sends the result to Yani in one step.
let quizGroup = 0; // unique radio-group name per rendered quiz

export function render(props, ctx) {
  const el = document.createElement('div');
  el.className = 'quiz-block';
  const label = document.createElement('div');
  label.className = 'quiz-block-label';
  label.textContent = props.quiz_label ?? 'Quiz';
  const q = document.createElement('p');
  q.className = 'quiz-question';
  q.textContent = props.question ?? '';

  const options = props.options ?? [];
  const name = `quiz-${quizGroup++}`;
  const optionsEl = document.createElement('div');
  optionsEl.className = 'quiz-choices';
  const feedback = document.createElement('div');
  feedback.className = 'quiz-feedback';
  const check = document.createElement('button');
  check.className = 'mentor-btn';
  check.textContent = 'Check answer';
  check.disabled = true;

  let chosen = -1;
  const rows = options.map((opt, i) => {
    const row = document.createElement('label');
    row.className = 'quiz-choice';
    const input = document.createElement('input');
    input.type = 'radio';
    input.name = name;
    input.addEventListener('change', () => { chosen = i; check.disabled = false; });
    const text = document.createElement('span');
    text.textContent = opt.text ?? '';
    row.append(input, text);
    optionsEl.appendChild(row);
    return { row, input };
  });

  check.addEventListener('click', () => {
    if (chosen < 0) return;
    const opt = options[chosen];
    rows.forEach(({ row, input }, j) => {
      input.disabled = true;
      if (options[j].correct) row.classList.add('opt-correct');
    });
    if (!opt.correct) rows[chosen].row.classList.add('opt-wrong');
    feedback.textContent = opt.explain ?? '';
    feedback.classList.add(opt.correct ? 'feedback-correct' : 'feedback-wrong');
    ctx.dispatchAction({ event: { name: 'quiz_result', context: {
      topic: props.topic ?? '', question: props.question ?? '',
      chosen: opt.text ?? '', correct: Boolean(opt.correct),
    } } });
    check.disabled = true;
    check.textContent = 'Sent to Yani ✓';
  });

  el.append(label, q, optionsEl, feedback, check);
  return el;
}
