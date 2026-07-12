// Minimal markdown -> DOM renderer for chat bubbles. Deliberately not a
// full parser and deliberately not innerHTML: every leaf is textContent,
// links are scheme-allowlisted, so model output can style text but can
// never inject markup. Covers what the model actually emits in chat:
// paragraphs, **bold**, *italic*, `code`, ``` fences, -/1. lists,
// # headings, [label](https://...) links.

function appendInline(parent, text) {
  const re = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*\n]+\*)|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
  let last = 0;
  let m;
  while ((m = re.exec(text))) {
    if (m.index > last) parent.appendChild(document.createTextNode(text.slice(last, m.index)));
    if (m[1]) {
      const code = document.createElement('code');
      code.textContent = m[1].slice(1, -1);
      parent.appendChild(code);
    } else if (m[2]) {
      const strong = document.createElement('strong');
      appendInline(strong, m[2].slice(2, -2));
      parent.appendChild(strong);
    } else if (m[3]) {
      const em = document.createElement('em');
      appendInline(em, m[3].slice(1, -1));
      parent.appendChild(em);
    } else {
      // m[4] label, m[5] href — regex already restricts to http(s)
      const a = document.createElement('a');
      a.href = m[5];
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = m[4];
      parent.appendChild(a);
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) parent.appendChild(document.createTextNode(text.slice(last)));
}

export function renderMarkdownInto(el, text) {
  el.replaceChildren();
  const lines = String(text ?? '').split('\n');
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim() === '') { i++; continue; }

    if (line.startsWith('```')) {
      const buf = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) buf.push(lines[i++]);
      i++; // closing fence (or end of a still-streaming block)
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      code.textContent = buf.join('\n');
      pre.appendChild(code);
      el.appendChild(pre);
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.*)/);
    if (heading) {
      // bubble headings render small: # -> h4 ... #### -> h6, capped
      const h = document.createElement(`h${Math.min(heading[1].length + 3, 6)}`);
      appendInline(h, heading[2]);
      el.appendChild(h);
      i++;
      continue;
    }

    const isUl = (l) => /^\s*[-*]\s+/.test(l);
    const isOl = (l) => /^\s*\d+[.)]\s+/.test(l);
    if (isUl(line) || isOl(line)) {
      const ordered = isOl(line);
      const list = document.createElement(ordered ? 'ol' : 'ul');
      while (i < lines.length && (ordered ? isOl(lines[i]) : isUl(lines[i]))) {
        const li = document.createElement('li');
        appendInline(li, lines[i].replace(ordered ? /^\s*\d+[.)]\s+/ : /^\s*[-*]\s+/, ''));
        list.appendChild(li);
        i++;
      }
      el.appendChild(list);
      continue;
    }

    // paragraph: contiguous plain lines, single newlines become <br>
    const p = document.createElement('p');
    let first = true;
    while (i < lines.length && lines[i].trim() !== ''
           && !lines[i].startsWith('```') && !/^(#{1,4})\s/.test(lines[i])
           && !isUl(lines[i]) && !isOl(lines[i])) {
      if (!first) p.appendChild(document.createElement('br'));
      appendInline(p, lines[i]);
      first = false;
      i++;
    }
    el.appendChild(p);
  }
}
