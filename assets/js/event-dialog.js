// Event details pop-up, shared by the event cards and the month calendar (see _includes/event-dialog.html).
// Everything that comes from the calendar is added with textContent or encoded into a link, never written as HTML.
(function () {
  const dlg = document.getElementById('event-dialog');
  if (!dlg) return;
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const title = document.getElementById('event-dialog-title');
  const body = document.getElementById('event-dialog-body');
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  const nice = day => { const [y, m, d] = day.split('-').map(Number); return DAYS[new Date(y, m - 1, d).getDay()] + ', ' + MONTHS[m - 1] + ' ' + d; };

  // ---- add to calendar ----
  const compact = day => day.replace(/-/g, '');                                          // 2026-11-20 -> 20261120
  const dayAfter = day => { const [y, m, d] = day.split('-').map(Number); return new Date(Date.UTC(y, m - 1, d + 1)).toISOString().slice(0, 10); };
  const stamp = () => new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');   // 20261108T170000Z

  // Start and end the way calendar apps want them. All-day events end the day AFTER their last day.
  function span(e) {
    if (e.all_day) return { allDay: true, start: compact(e.date), end: compact(dayAfter(e.end_date || e.date)) };
    return e.start_utc ? { allDay: false, start: e.start_utc, end: e.end_utc } : null;
  }

  function notes(e) {
    const parts = [];
    if (e.tentative) parts.push('The date or time is still to be confirmed. Check the PTA website for updates.');
    if (e.description) parts.push(e.description);
    if (/^https?:\/\//i.test(e.url || '') && (e.description || '').indexOf(e.url) < 0) parts.push('More information: ' + e.url);
    parts.push('Monte Vista PTA events: ' + dlg.dataset.eventsUrl);
    return parts.join('\n\n');
  }

  function googleLink(e, s) {
    const q = { action: 'TEMPLATE', text: e.title, dates: s.start + '/' + s.end, details: notes(e), location: e.location || e.place || '' };
    let url = 'https://calendar.google.com/calendar/render?' + Object.keys(q).map(k => k + '=' + encodeURIComponent(q[k])).join('&');
    if (!s.allDay) url += '&ctz=America%2FLos_Angeles';
    return url;
  }

  function outlookLink(e, s) {
    const iso = c => c.slice(0, 4) + '-' + c.slice(4, 6) + '-' + c.slice(6, 8) + (s.allDay ? '' : 'T' + c.slice(9, 11) + ':' + c.slice(11, 13) + ':' + c.slice(13, 15) + 'Z');
    const q = { path: '/calendar/action/compose', rru: 'addevent', subject: e.title, startdt: iso(s.start), enddt: iso(s.end), body: notes(e), location: e.location || e.place || '' };
    if (s.allDay) q.allday = 'true';
    return 'https://outlook.live.com/calendar/0/deeplink/compose?' + Object.keys(q).map(k => k + '=' + encodeURIComponent(q[k])).join('&');
  }

  // iCalendar text rules: escape \ ; , and newlines, and fold lines longer than 75 bytes.
  const esc = t => String(t).replace(/\\/g, '\\\\').replace(/;/g, '\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n');
  function fold(line) {
    const enc = new TextEncoder(), out = [];
    let cur = '', bytes = 0;
    for (const ch of line) {
      const n = enc.encode(ch).length;
      if (bytes + n > (out.length ? 74 : 75)) { out.push(cur); cur = ''; bytes = 0; }
      cur += ch; bytes += n;
    }
    out.push(cur);
    return out.join('\r\n ');
  }
  function icsFile(e, s) {
    const lines = [
      'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Monte Vista PTA//Website//EN', 'CALSCALE:GREGORIAN', 'BEGIN:VEVENT',
      'UID:' + e.id + '@montevistapta.org', 'DTSTAMP:' + stamp(), 'SUMMARY:' + esc(e.title),
      s.allDay ? 'DTSTART;VALUE=DATE:' + s.start : 'DTSTART:' + s.start,
      s.allDay ? 'DTEND;VALUE=DATE:' + s.end : 'DTEND:' + s.end,
    ];
    if (e.location || e.place) lines.push('LOCATION:' + esc(e.location || e.place));
    lines.push('DESCRIPTION:' + esc(notes(e)));
    if (e.tentative) lines.push('STATUS:TENTATIVE');
    lines.push('END:VEVENT', 'END:VCALENDAR');
    return lines.map(fold).join('\r\n') + '\r\n';
  }
  function download(e, s) {
    const url = URL.createObjectURL(new Blob([icsFile(e, s)], { type: 'text/calendar;charset=utf-8' }));
    const a = el('a'); a.href = url; a.download = (e.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'event') + '.ics';
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function addToCalendar(e) {
    const s = span(e);
    if (!s) return null;
    const box = el('div', 'add-cal');
    box.append(el('h4', null, 'Add to my calendar'));
    const row = el('p', 'add-cal-row');
    [['Google Calendar', googleLink(e, s)], ['Outlook.com', outlookLink(e, s)]].forEach(([label, href]) => {
      const a = el('a', 'btn btn-soft btn-sm', label);
      a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer';
      row.append(a);
    });
    const file = el('button', 'btn btn-soft btn-sm', 'Apple / other (.ics file)'); file.type = 'button';
    file.addEventListener('click', () => download(e, s));
    row.append(file);
    box.append(row);
    if (e.tentative) box.append(el('p', 'meta', 'The date or time is not final yet, so check back here before the event.'));
    return box;
  }

  // ---- the pop-up ----
  function eventBox(e) {
    const box = el('div', 'cal-event');
    box.append(el('h3', null, (e.emoji ? e.emoji + ' ' : '') + e.title));
    const when = e.end_date ? nice(e.date) + ' to ' + nice(e.end_date) : e.time;
    box.append(el('p', 'meta', when + (e.end_date && e.time && !e.all_day ? ', ' + e.time : '') + (e.place ? ' · ' + e.place : '')));
    if (e.tentative) box.append(el('p', null, 'The date or time is still to be confirmed.'));
    (e.description || '').split('\n').filter(Boolean).forEach(line => box.append(el('p', null, line)));
    if (/^https?:\/\//i.test(e.url || '')) {
      const a = el('a', null, 'More information');
      a.href = e.url; a.target = '_blank'; a.rel = 'noopener noreferrer';
      box.append(el('p')); box.lastChild.append(a);
    }
    const add = addToCalendar(e);
    if (add) box.append(add);
    return box;
  }

  function open(heading, list) {
    title.textContent = heading;
    body.replaceChildren(...list.map(eventBox));
    dlg.showModal();
  }
  window.mvEvents = { open, nice };

  // ---- event cards (the horizontal cards on the home page and the Events page) ----
  // The card is a link to the Events page, which is what happens without JavaScript or before the data has loaded.
  const cards = document.querySelectorAll('.hcard[data-event-id]');
  if (!cards.length) return;
  let byId = null;
  fetch(dlg.dataset.src).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(list => { byId = new Map(list.map(e => [e.id, e])); })
    .catch(() => {});
  cards.forEach(card => {
    card.setAttribute('aria-haspopup', 'dialog');
    card.addEventListener('click', ev => {
      if (ev.defaultPrevented || ev.button || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;   // keep "open in new tab" working
      const e = byId && byId.get(card.dataset.eventId);
      if (!e) return;
      ev.preventDefault();
      open(nice(e.date), [e]);
    });
  });
})();
