// CodeBlock — cool-blue listing, house tokenizer (no library), fill-in blanks.
const KEYWORDS = new Set([
  'def', 'class', 'return', 'if', 'elif', 'else', 'for', 'while', 'import',
  'from', 'in', 'not', 'and', 'or', 'lambda', 'try', 'except', 'finally',
  'with', 'as', 'yield', 'pass', 'raise', 'None', 'True', 'False', 'print',
  'const', 'let', 'var', 'function', 'new', 'await', 'async', 'null', 'true', 'false',
]);

const TOKEN = /(#[^\n]*|\/\/[^\n]*)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)|\b(\d[\d_.]*)\b|\b([A-Za-z_][A-Za-z0-9_]*)\b/g;

function highlightInto(codeEl, source) {
  let last = 0;
  for (const m of source.matchAll(TOKEN)) {
    if (m.index > last) codeEl.append(source.slice(last, m.index));
    const [full, comment, str, num, word] = m;
    let cls = null;
    if (comment) cls = 'syn-cm';
    else if (str) cls = 'syn-str';
    else if (num) cls = 'syn-num';
    else if (word && KEYWORDS.has(word)) cls = 'syn-kw';
    else if (word && source.slice(m.index + full.length).trimStart().startsWith('(')) cls = 'syn-fn';
    if (cls) {
      const span = document.createElement('span');
      span.className = cls;
      span.textContent = full;
      codeEl.appendChild(span);
    } else {
      codeEl.append(full);
    }
    last = m.index + full.length;
  }
  if (last < source.length) codeEl.append(source.slice(last));
}

export function render(props) {
  const el = document.createElement('div');
  el.className = 'code-block';
  const header = document.createElement('div');
  header.className = 'code-block-header';
  const t = document.createElement('span');
  t.textContent = props.title ?? '';
  const lang = document.createElement('span');
  lang.textContent = props.language ?? '';
  header.append(t, lang);
  const pre = document.createElement('pre');
  const codeEl = document.createElement('code');
  pre.appendChild(codeEl);
  el.append(header, pre);

  const segments = String(props.code ?? '').split(/_{4,}/);
  segments.forEach((seg, i) => {
    highlightInto(codeEl, seg);
    if (i < segments.length - 1) {
      const blank = document.createElement('span');
      blank.className = 'blank';
      blank.textContent = props.blank_hint || 'you fill this in';
      codeEl.appendChild(blank);
    }
  });
  return el;
}
