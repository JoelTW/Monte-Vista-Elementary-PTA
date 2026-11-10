// Live preview for the editor: draws the home page banner with the site's own styles.
CMS.registerPreviewStyle('../assets/css/styles.css');
CMS.registerPreviewTemplate('home', ({ entry, getAsset }) => {
  const hero = (entry.getIn(['data', 'hero']) || new Map()).toJS ? entry.getIn(['data', 'hero']).toJS() : {};
  const photo = hero.photo ? getAsset(hero.photo) : null;
  const style = photo ? { background: `url('${photo}') ${hero.photo_position || 'center'}/cover` } : {};
  return h('section', { className: 'hero' },
    h('div', { className: 'wrap' }, h('div', {},
      h('h1', {}, hero.line1, h('em', {}, hero.line2)),
      h('p', { className: 'lead' }, hero.lead),
      h('div', { className: 'btns' },
        h('a', { className: 'btn btn-gold' }, hero.primary_button),
        h('a', { className: 'btn btn-outline' }, hero.secondary_button)))),
    h('div', { className: 'photo-wrap' }, h('div', { className: 'photo', style })));
});

// Get Involved: draws each section with the site's own styles (same markup as _includes/column.html).
const giButtons = (list) => (list || []).map((b) =>
  h('p', {}, h('a', { className: 'btn btn-' + (b.style || 'gold') }, b.label)));

const giColumn = (c, getAsset) => {
  if (c.type === 'text') {
    return h('div', {},
      h('h2', {}, c.heading), h('p', {}, c.text),
      c.form === 'volunteer' ? h('p', { className: 'note' }, '[Volunteer sign-up form appears here]') : null,
      giButtons(c.buttons),
      c.note ? h('p', { className: 'note' }, c.note) : null);
  }
  // getAsset finds pictures the editor knows about; others fall back to the normal site path.
  const asset = c.image ? getAsset(c.image) : null;
  const src = asset ? asset.toString() : (c.image ? '..' + c.image : '');
  if (c.type === 'image') {
    return h('div', { className: 'poster-box' }, h('img', { className: 'poster-img', src, alt: c.alt }));
  }
  if (c.type === 'card') {
    return h('div', { className: 'card' }, h('div', { className: 'pad' },
      h('h3', {}, c.title), h('img', { src, width: c.width, alt: c.alt })));
  }
  return null;
};

CMS.registerPreviewTemplate('get_involved', ({ entry, getAsset }) => {
  try {
    const data = entry.get('data').toJS();
    return h('div', {}, (data.sections || []).map((s) =>
      h('section', { className: 'section' + (s.tint ? ' ' + s.tint : '') },
        h('div', { className: 'wrap' + ((s.columns || []).length === 2 ? ' two' : '') },
          (s.columns || []).map((c) => giColumn(c, getAsset))))));
  } catch (e) {
    return h('p', { className: 'note' }, 'Preview problem: ' + e.message);
  }
});
