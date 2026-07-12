// Shared MathJax hook. MathJax loads async from the CDN; lessons can arrive
// first. Retry briefly, then give up quietly (TeX stays visible as source).
export function typeset(el) {
  let tries = 0;
  const attempt = () => {
    if (window.MathJax?.typesetPromise) {
      window.MathJax.typesetPromise([el]).catch((e) => console.warn('MathJax:', e));
    } else if (tries++ < 40) {
      setTimeout(attempt, 250);
    }
  };
  requestAnimationFrame(attempt);
}
