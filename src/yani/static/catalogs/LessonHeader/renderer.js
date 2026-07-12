// LessonHeader — lesson page furniture: eyebrow, title, subtitle, loop plan.
export function render(props) {
  const el = document.createElement('div');
  el.className = 'lesson-header';
  const eyebrow = document.createElement('div');
  eyebrow.className = 'lesson-eyebrow';
  eyebrow.textContent = props.eyebrow ?? '';
  const h1 = document.createElement('h1');
  h1.textContent = props.title ?? '';
  const sub = document.createElement('p');
  sub.className = 'lesson-subtitle';
  const em = document.createElement('em');
  em.textContent = props.subtitle ?? '';
  sub.appendChild(em);
  el.append(eyebrow, h1, sub);
  // loop_plan is teacher shorthand — the learner-facing Overview passes null
  // and no plan line renders (spec 0002)
  if (props.loop_plan) {
    const plan = document.createElement('p');
    plan.className = 'loop-plan';
    plan.textContent = 'Loop plan ';
    const code = document.createElement('code');
    code.textContent = props.loop_plan;
    plan.appendChild(code);
    el.appendChild(plan);
  }
  return el;
}
