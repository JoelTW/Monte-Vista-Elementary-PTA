// Month calendar: reads assets/data/events.json (made from the PTA's calendar) and draws a month at a time.
// All text from the calendar is added with textContent, never as HTML.
(function () {
  const root = document.querySelector('.cal');
  if (!root) return;
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const pad = n => String(n).padStart(2, '0');
  const iso = (y, m, d) => y + '-' + pad(m + 1) + '-' + pad(d);          // m is 0-11
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  let events = [], year, month, minKey, maxKey, grid, title, prev, next;

  const onDay = day => events.filter(e => e.date <= day && day <= (e.end_date || e.date));
  const nice = day => window.mvEvents.nice(day);
  const key = (y, m) => y * 12 + m;

  const openDay = day => window.mvEvents.open(nice(day), onDay(day));

  function draw() {
    title.textContent = MONTHS[month] + ' ' + year;
    prev.disabled = key(year, month) <= minKey;
    next.disabled = key(year, month) >= maxKey;
    grid.replaceChildren();
    const first = new Date(year, month, 1).getDay();
    const days = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    const todayIso = iso(today.getFullYear(), today.getMonth(), today.getDate());
    let tr = el('tr');
    for (let i = 0; i < first; i++) tr.append(el('td', 'out'));
    for (let d = 1; d <= days; d++) {
      if (tr.children.length === 7) { grid.append(tr); tr = el('tr'); }
      const day = iso(year, month, d);
      const list = onDay(day);
      const td = el('td', day === todayIso ? 'is-today' : '');
      if (list.length === 0) {
        td.append(el('span', 'cal-num', d));
      } else {
        const b = el('button', 'cal-day'); b.type = 'button';
        b.setAttribute('aria-label', nice(day) + ': ' + list.map(e => e.title).join(', '));
        b.append(el('span', 'cal-num', d));
        list.slice(0, 2).forEach(e => b.append(el('span', 'cal-chip' + (e.tentative ? ' tent' : ''), e.title)));
        if (list.length > 2) b.append(el('span', 'cal-chip more', '+' + (list.length - 2) + ' more'));
        const dots = el('span', 'cal-dots'); list.slice(0, 4).forEach(() => dots.append(el('span', 'cal-dot'))); b.append(dots);
        b.addEventListener('click', () => openDay(day));
        td.append(b);
      }
      if (day === todayIso) td.setAttribute('aria-current', 'date');
      tr.append(td);
    }
    while (tr.children.length < 7) tr.append(el('td', 'out'));
    grid.append(tr);
  }

  function go(delta) { const d = new Date(year, month + delta, 1); year = d.getFullYear(); month = d.getMonth(); draw(); }

  function build() {
    const now = new Date();
    year = now.getFullYear(); month = now.getMonth();
    const keys = events.map(e => { const [y, m] = e.date.split('-').map(Number); return key(y, m - 1); });
    minKey = Math.min(key(year, month), ...keys);
    maxKey = Math.max(key(year, month), ...events.map(e => { const [y, m] = (e.end_date || e.date).split('-').map(Number); return key(y, m - 1); }));
    const head = el('div', 'cal-head');
    prev = el('button', 'cal-nav', '‹'); prev.type = 'button'; prev.setAttribute('aria-label', 'Previous month');
    next = el('button', 'cal-nav', '›'); next.type = 'button'; next.setAttribute('aria-label', 'Next month');
    const todayBtn = el('button', 'btn btn-soft btn-sm', 'Today'); todayBtn.type = 'button';
    title = el('h3'); title.setAttribute('aria-live', 'polite');
    head.append(prev, title, next, todayBtn);
    const table = el('table', 'cal-grid');
    table.append(el('caption', 'sr', 'Month calendar. Days with events are buttons.'));
    const thead = el('thead'), htr = el('tr');
    DAYS.forEach(n => { const th = el('th', null, n.slice(0, 3)); th.scope = 'col'; th.title = n; htr.append(th); });
    thead.append(htr); grid = el('tbody'); table.append(thead, grid);
    root.replaceChildren(head, table);
    prev.addEventListener('click', () => go(-1));
    next.addEventListener('click', () => go(1));
    todayBtn.addEventListener('click', () => { const n = new Date(); year = n.getFullYear(); month = n.getMonth(); draw(); });
    draw();
  }

  fetch(root.dataset.src).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(data => { events = data; build(); })
    .catch(() => { root.replaceChildren(el('p', null, 'The calendar could not be loaded. The upcoming events are listed below.')); });
})();
