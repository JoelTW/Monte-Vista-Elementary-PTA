// Live preview for the editor: draws the home page and every sections page with the site's own styles.
CMS.registerPreviewStyle('../assets/css/styles.css');
CMS.registerPreviewTemplate('home', ({ entry, getAsset }) => {
  try {
    const d = entry.get('data').toJS();
    const pic = (path) => {
      if (!path) return '';
      const asset = getAsset(path);
      return asset ? asset.toString() : '..' + path;
    };
    const bg = (path, pos) => (path ? { background: `url('${pic(path)}') ${pos || 'center'}/cover` } : {});
    const hero = d.hero || {};
    const pres = d.president || {};
    const diff = d.difference || {};
    const words = (pres.message || '').replace('[[photo]]', '').replace(/[*#_\[\]]/g, '').replace(/\([^)]*\)/g, '').split(/\s+/).filter(Boolean);
    const n = pres.preview_words || 45;
    const teaser = words.slice(0, n).join(' ') + (words.length > n ? '…' : '');
    return h('div', {},
      h('section', { className: 'hero' },
        h('div', { className: 'wrap' }, h('div', {},
          h('h1', {}, hero.line1, h('em', {}, hero.line2)),
          h('p', { className: 'lead' }, hero.lead),
          h('div', { className: 'btns' },
            h('a', { className: 'btn btn-gold' }, hero.primary_button),
            h('a', { className: 'btn btn-outline' }, hero.secondary_button)))),
        h('div', { className: 'photo-wrap' }, h('div', { className: 'photo', style: bg(hero.photo, hero.photo_position) }))),
      h('div', { className: 'wrap' },
        h('section', { className: 'pres' },
          h('div', { className: 'avatar', style: bg(pres.photo, 'center 35%') }, pres.photo ? '' : pres.avatar),
          h('div', {}, h('h2', {}, pres.heading), h('p', {}, teaser),
            h('p', {}, h('button', { className: 'btn btn-blue btn-sm', type: 'button' }, 'Read the full message'))),
          h('p', { className: 'script' }, pres.tagline))),
      h('section', { className: 'section' }, h('div', { className: 'wrap' },
        h('div', { className: 'head-row' }, h('h2', {}, d.events_heading), h('a', {}, 'View full calendar →')),
        h('p', { className: 'note' }, '[The next three events from the calendar appear here]'))),
      h('section', { className: 'section', style: { paddingTop: 0 } }, h('div', { className: 'wrap' },
        h('div', { className: 'cta4' }, (d.cards || []).map((c, i) =>
          h('a', { key: i, className: 'cta c-' + (c.color || 'sky') },
            h('span', { className: 'ic' }, c.icon), h('h3', {}, c.title), h('p', {}, c.text), h('b', {}, c.link_text)))))),
      h('section', { className: 'section' }, h('div', { className: 'wrap diff' },
        h('div', {}, h('h2', {}, diff.heading), h('p', {}, diff.text)),
        h('div', { className: 'diff-items' }, (diff.items || []).map((f, i) =>
          h('div', { key: i }, h('span', { className: 'ic' }, f.icon), f.title, h('small', {}, f.text)))))),
      h('section', { className: 'section' }, h('div', { className: 'wrap' },
        h('div', { className: 'head-row' }, h('h2', {}, d.moments_heading), h('a', {}, 'View photo gallery →')),
        h('div', { className: 'moments' }, (d.moments || []).map((m, i) =>
          h('div', { key: i, className: m.tint, style: bg(m.image) }, m.image ? '' : m.emoji))))),
      h('section', { className: 'section sky' }, h('div', { className: 'wrap' },
        h('h2', {}, d.sponsors_heading),
        h('div', { className: 'sponsors' }, (d.sponsors || []).map((s, i) =>
          s.logo ? h('a', { key: i, className: 'ph' }, h('img', { src: pic(s.logo), alt: s.name, style: { maxHeight: '60px' } }))
                 : h('div', { key: i, className: 'ph' }, s.name))))));
  } catch (e) {
    return h('p', {}, 'Preview problem: ' + e.message);
  }
});

// Page previews: one renderer for every page that is a list of sections. Same markup as _includes/block.html.
const NOTE = (text) => h('p', { className: 'note' }, text);
const LINK_NOTE = {
  team: '[The board and chairs appear here]',
  calendar: '[The month calendar and subscribe buttons appear here]',
  upcoming: '[The upcoming events list appears here]',
  social_feed: '[The Facebook and Instagram links appear here]',
};

const renderBlock = (b, getAsset) => {
  const pic = (path) => {
    if (!path) return '';
    const asset = getAsset(path);
    return asset ? asset.toString() : '..' + path;
  };
  switch (b.type) {
    case 'heading': return b.level === 3 ? h('h3', {}, b.text) : h('h2', {}, b.text);
    case 'paragraph': return h('p', b.space_above ? { style: { marginTop: '20px' } } : {}, b.text);
    case 'link_paragraph': return h('p', {}, b.text + ' ', h('a', { href: '#' }, b.link_text), '.');
    case 'note': return NOTE(b.text);
    case 'email_note': return NOTE((b.text || '') + ' (email address)');
    case 'email_link': return h('p', {}, h('a', { href: '#' }, '(email address)'));
    case 'chips': return h('ul', { className: 'chips' }, (b.items || []).map((e) => h('li', {}, e)));
    case 'steps': return h('ol', { className: 'steps' }, (b.items || []).map((e) => h('li', {}, e)));
    case 'tips': return h('ul', { className: 'tips' }, (b.items || []).map((e) => h('li', {}, e)));
    case 'buttons': {
      const btns = (b.items || []).map((x) => h('a', { className: 'btn btn-' + (x.style || 'gold') }, x.label));
      if (b.layout === 'stacked') return h('div', {}, btns.map((x) => h('p', {}, x)));
      return h('p', {}, btns.reduce((acc, x, i) => (i ? acc.concat([' ', x]) : [x]), []));
    }
    case 'image': {
      const src = pic(b.image);
      return h('img', { className: b.style === 'poster' ? 'poster-img' : '', src, width: b.width, alt: b.alt });
    }
    case 'placeholder': return h('div', { className: 'ph', style: { minHeight: (b.min_height || 260) + 'px' } }, b.text);
    case 'placeholder_grid': return h('div', { className: 'grid3' }, [1, 2, 3].map(() => h('div', { className: 'ph' }, b.text)));
    case 'role_cards': return h('div', { className: 'cta4' }, (b.items || []).map((r) =>
      h('div', { className: 'cta c-' + (r.color || 'sky'), style: { cursor: 'default' } },
        h('span', { className: 'ic' }, r.icon), h('h3', {}, r.title), h('p', {}, r.text))));
    case 'form': return NOTE('[The ' + b.form + ' form appears here]');
    case 'contact_details': return h('div', {}, h('h2', {}, b.heading), h('p', {}, 'Email, address and links appear here'),
      h('h3', {}, b.board_heading), h('p', {}, b.board_text));
    default: return NOTE(LINK_NOTE[b.type] || '');
  }
};

const renderColumn = (c, getAsset) => {
  const inner = (c.blocks || []).map((b) => renderBlock(b, getAsset));
  if (c.kind === 'card') return h('div', { className: 'card' }, h('div', { className: 'pad' }, inner));
  if (c.kind === 'poster') return h('div', { className: 'poster-box' }, inner);
  if (c.kind === 'bare') return h('div', {}, inner);
  return h('div', {}, inner);
};

const sectionsPreview = ({ entry, getAsset }) => {
  try {
    const data = entry.get('data').toJS();
    return h('div', {}, (data.sections || []).map((s) =>
      h('section', { className: 'section' + (s.tint ? ' ' + s.tint : '') },
        h('div', { className: 'wrap' + ((s.columns || []).length === 2 ? ' two' : '') },
          (s.columns || []).map((c) => renderColumn(c, getAsset))))));
  } catch (e) {
    return h('p', { className: 'note' }, 'Preview problem: ' + e.message);
  }
};

['about', 'events', 'get_involved', 'give', 'yearbook', 'contact'].forEach((name) =>
  CMS.registerPreviewTemplate(name, sectionsPreview));

// Team page preview: same markup as _includes/team-card.html.
CMS.registerPreviewTemplate('team', ({ entry, getAsset }) => {
  try {
    const d = entry.get('data').toJS();
    const pic = (path) => {
      const asset = getAsset(path);
      return asset ? asset.toString() : '..' + path;
    };
    return h('section', { className: 'section' }, h('div', { className: 'wrap' },
      h('p', {}, d.intro),
      (d.groups || []).map((g, gi) =>
        h('div', { key: gi },
          h('h3', { className: 'month' }, g.heading),
          h('div', { className: 'team-grid' }, (g.members || []).map((m, i) =>
            h('article', { key: i, className: 'person' + (m.open ? ' open' : '') },
              h('div', { className: 'avatar sm', style: m.photo ? { background: `url('${pic(m.photo)}') center 35%/cover` } : {} }, m.photo ? '' : (m.icon || '🙂')),
              h('p', { className: 'role' }, m.role),
              m.open ? h('h3', {}, 'Open position')
                : m.name ? h('h3', {}, m.name) : h('h3', { className: 'muted' }, 'Name coming soon'),
              h('p', {}, m.blurb),
              m.ask_me_about ? h('p', { className: 'ask' }, h('b', {}, 'Ask me about: '), m.ask_me_about) : null,
              m.open ? h('p', {}, h('a', { className: 'btn btn-blue btn-sm' }, 'Could this be you?'))
                : m.email ? h('p', {}, h('a', {}, m.email)) : null)))))));
  } catch (e) {
    return h('p', { className: 'note' }, 'Preview problem: ' + e.message);
  }
});
