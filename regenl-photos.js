/* ReGeNL SkoHub PoC: inject figures from foaf:depiction into concept pages.
   Independent of the SkoHub source code and safe when no photo exists. */
(() => {
  'use strict';
  const base = '/regenl-vocabulary-poc/';
  let entries = {};
  let lastPath = '';
  let busy = false;
  const style = document.createElement('style');
  style.textContent = `
    figure.regenl-concept-photo { margin: 1rem 0 1.5rem; max-width: 660px; }
    figure.regenl-concept-photo img { width: 100%; height: auto; max-height: 420px;
      object-fit: cover; border-radius: 8px; display: block; }
    figure.regenl-concept-photo figcaption { margin-top: .45rem; font-size: .82rem;
      color: #555; line-height: 1.45; }
    figure.regenl-concept-photo a { color: inherit; text-decoration: underline; }
  `;
  document.head.appendChild(style);

  function findEntry() {
    const path = decodeURI(window.location.pathname).replace(/\/$/, '').replace(/\.html$/, '');
    const exact = Object.entries(entries).find(([uri]) => {
      try {
        const u = new URL(uri);
        return decodeURI(u.pathname).replace(/\/$/, '') === path;
      } catch (_) { return false; }
    });
    return exact ? exact[1] : null;
  }

  function render() {
    if (busy) return;
    busy = true;
    try {
      const entry = findEntry();
      const present = document.querySelector('.regenl-concept-photo');
      if (!entry) { if (present) present.remove(); return; }
      if (present) return;
      const heading = document.querySelector('main h1, main h2, article h1, article h2');
      if (!heading) return;
      const figure = document.createElement('figure');
      figure.className = 'regenl-concept-photo';
      const img = document.createElement('img');
      img.src = entry.image;
      img.alt = heading.textContent.trim();
      img.loading = 'lazy';
      img.referrerPolicy = 'no-referrer';
      figure.appendChild(img);
      if (entry.credit || entry.source) {
        const caption = document.createElement('figcaption');
        if (entry.credit) caption.appendChild(document.createTextNode(entry.credit + ' '));
        if (entry.source && /^https:\/\//.test(entry.source)) {
          const link = document.createElement('a');
          link.href = entry.source;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.textContent = 'Bron en licentie';
          caption.appendChild(link);
        }
        figure.appendChild(caption);
      }
      heading.insertAdjacentElement('afterend', figure);
    } finally { busy = false; }
  }
  let scheduled = false;
  function update() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      const current = window.location.pathname;
      if (current !== lastPath) {
        lastPath = current;
        document.querySelectorAll('.regenl-concept-photo').forEach(n => n.remove());
      }
      render();
    });
  }
  fetch(base + 'regenl-photos.json', { cache: 'no-store' })
    .then(response => { if (!response.ok) throw new Error('photo metadata unavailable'); return response.json(); })
    .then(data => { entries = data; update(); new MutationObserver(update).observe(document.body, {childList:true,subtree:true}); })
    .catch(error => console.warn('ReGeNL photo enhancement:',error));
})();
