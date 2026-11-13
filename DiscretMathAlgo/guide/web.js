(() => {
  const menu = document.querySelector('#menu-toggle');
  menu.addEventListener('click', () => {
    const open = document.body.classList.toggle('nav-open');
    menu.setAttribute('aria-expanded', String(open));
  });
  document.querySelectorAll('nav a').forEach(link => link.addEventListener('click', () => {
    document.body.classList.remove('nav-open'); menu.setAttribute('aria-expanded', 'false');
  }));
  const progress = document.querySelector('#progress');
  let scheduled = false;
  function updateProgress() {
    const span = document.documentElement.scrollHeight - innerHeight;
    progress.style.width = `${span > 0 ? Math.min(100, Math.max(0, scrollY / span * 100)) : 0}%`;
    scheduled = false;
  }
  addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(updateProgress); } }, {passive:true});
  addEventListener('resize', updateProgress); updateProgress();
  const navLinks = [...document.querySelectorAll('.chapter-link')];
  const observer = new IntersectionObserver(entries => {
    const entry = entries.filter(item => item.isIntersecting).sort((a,b) => a.boundingClientRect.top-b.boundingClientRect.top)[0];
    if (!entry) return;
    navLinks.forEach(link => {
      if (link.hash === `#${entry.target.id}`) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
  }, {rootMargin:'-8% 0px -65% 0px'});
  document.querySelectorAll('main section').forEach(section => observer.observe(section));
  const dialog = document.querySelector('#figure-dialog');
  const target = document.querySelector('#dialog-figure');
  const title = document.querySelector('#dialog-title');
  let opener;
  function openFigure(figure) {
    opener = document.activeElement;
    target.replaceChildren(figure.querySelector('svg').cloneNode(true));
    title.textContent = figure.querySelector('figcaption').textContent;
    dialog.showModal();
  }
  document.querySelectorAll('figure').forEach(figure => {
    const button = document.createElement('button'); button.type = 'button'; button.className = 'figure-zoom';
    button.textContent = 'Увеличить схему';
    button.setAttribute('aria-label', `Увеличить: ${figure.querySelector('figcaption').textContent}`);
    button.addEventListener('click', () => openFigure(figure));
    figure.querySelector('svg').addEventListener('click', () => openFigure(figure));
    figure.append(button);
  });
  document.querySelector('#dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => { target.replaceChildren(); opener?.focus(); });
  document.querySelector('#print-button').addEventListener('click', () => print());
})();

// An offline trace of the Z -> sp' -> KMP path used by the chapter.
(() => {
  const lab = document.querySelector('#kmp-lab');
  if (!lab) return;
  const examples = {
    fallback: {pattern: 'abacaba', text: 'ababacaba'},
    skip: {pattern: 'abacaba', text: 'abacac'},
    overlap: {pattern: 'abacaba', text: 'abacabacaba'}
  };
  function preprocess(pattern) {
    const z = Array(pattern.length).fill(0);
    z[0] = pattern.length;
    let left = 0, right = 0;
    for (let i = 1; i < pattern.length; i++) {
      if (i < right) z[i] = Math.min(right - i, z[i - left]);
      while (i + z[i] < pattern.length && pattern[z[i]] === pattern[i + z[i]]) z[i]++;
      if (i + z[i] > right) { left = i; right = i + z[i]; }
    }
    const sp = Array(pattern.length).fill(0);
    for (let j = pattern.length - 1; j >= 1; j--) {
      if (z[j] > 0) sp[j + z[j] - 1] = z[j];
    }
    return {z, sp};
  }
  function makeTrace(pattern, text, sp) {
    const events = [], answers = [];
    let i = 0, q = 0;
    function save(message) { events.push({i, q, message, answers: [...answers]}); }
    save('Начало: i = 0, q = 0. Сравним первый символ текста с началом образца.');
    while (i < text.length) {
      if (text[i] === pattern[q]) {
        const message = `T[${i}] = ${text[i]} совпал с P[${q}]. Продвигаем i и q на один.`;
        i++; q++;
        save(message);
        if (q === pattern.length) {
          answers.push(i - pattern.length);
          save(`Полное совпадение: начало ${i} − ${pattern.length} = ${i - pattern.length}. Сохраним границу для следующего вхождения.`);
          q = sp[q - 1];
          save(`После ответа q = sp′[${pattern.length - 1}] = ${q}. Индекс текста i = ${i} не изменился.`);
        }
      } else if (q > 0) {
        const old = q;
        q = sp[q - 1];
        save(`Несовпадение T[${i}] = ${text[i]} с P[${old}] = ${pattern[old]}. Откат ${old} → sp′[${old - 1}] = ${q}. Тот же символ текста ещё нужно проверить.`);
      } else {
        const old = i;
        i++;
        save(`T[${old}] = ${text[old]} не равен P[0] = ${pattern[0]}. При q = 0 сдвигаем индекс текста: i = ${i}.`);
      }
    }
    save('Текст закончился. Все найденные позиции показаны ниже.');
    return events;
  }
  const select = lab.querySelector('#kmp-example');
  const prev = lab.querySelector('#kmp-prev');
  const next = lab.querySelector('#kmp-next');
  const reset = lab.querySelector('#kmp-reset');
  let events, index, example;
  function render() {
    const event = events[index];
    lab.querySelector('#kmp-event').textContent = event.message;
    lab.querySelector('#kmp-result').textContent = `i = ${event.i}; q = ${event.q}; найденные начала: [${event.answers.join(', ')}]`;
    lab.querySelector('#kmp-counter').textContent = `Шаг ${index + 1} из ${events.length}`;
    prev.disabled = index === 0;
    next.disabled = index === events.length - 1;
    const alignment = lab.querySelector('#kmp-alignment');
    const table = document.createElement('table');
    table.className = 'kmp-strip';
    const shift = event.i - event.q;
    const count = Math.max(example.text.length + 1, shift + example.pattern.length);
    const rows = [
      ['Индекс', col => String(col)],
      ['Текст', col => col < example.text.length ? example.text[col] : col === example.text.length ? '∅' : ''],
      ['Образец', col => col >= shift && col < shift + example.pattern.length ? example.pattern[col - shift] : '']
    ];
    for (const [label, value] of rows) {
      const row = document.createElement('tr');
      const head = document.createElement('th'); head.scope = 'row'; head.textContent = label;
      row.append(head);
      for (let col = 0; col < count; col++) {
        const cell = document.createElement('td'); cell.textContent = value(col);
        if (label !== 'Индекс' && col >= shift && col < event.i) cell.classList.add('kmp-matched');
        if (col === event.i) cell.classList.add('kmp-current');
        row.append(cell);
      }
      table.append(row);
    }
    alignment.replaceChildren(table);
  }
  function load() {
    example = examples[select.value];
    const {z, sp} = preprocess(example.pattern);
    lab.querySelector('#kmp-arrays').textContent = `P = ${example.pattern}; Z = [${z.join(', ')}]; sp′ = [${sp.join(', ')}]. Синяя рамка — текущая позиция текста i; зелёный фон — уже совпавшая часть.`;
    events = makeTrace(example.pattern, example.text, sp); index = 0; render();
  }
  select.addEventListener('change', load);
  prev.addEventListener('click', () => { if (index > 0) { index--; render(); } });
  next.addEventListener('click', () => { if (index < events.length - 1) { index++; render(); } });
  reset.addEventListener('click', () => { index = 0; render(); });
  load();
})();
