"""Add a Qualtrics feedback modal to each ReGeNL SKOS concept page.

GitHub Actions: python scripts/add_regenl_feedback.py public data
Requires: rdflib (already installed by 'Add ReGeNL concept images').
Does not change SKOS input files, photos, or Gatsby assets.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
import sys

from rdflib import Graph, Literal, Namespace, RDF, URIRef

SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
PUBLIC = Path(sys.argv[1] if len(sys.argv) > 1 else 'public')
DATA = Path(sys.argv[2] if len(sys.argv) > 2 else 'data')
FORM = 'https://wur.az1.qualtrics.com/jfe/form/SV_82eRCHukHVmXvsW'
SCRIPT_NAME = 'regenl-feedback.js'

if not PUBLIC.is_dir() or not DATA.is_dir():
    raise SystemExit('Expected public/ and data/ directories')

concepts = {}
for ttl in sorted(DATA.rglob('*.ttl')):
    graph = Graph()
    graph.parse(ttl, format='turtle')
    for concept in set(graph.subjects(RDF.type, SKOS.Concept)):
        if not isinstance(concept, URIRef):
            continue
        uri = str(concept)
        path = unquote(urlsplit(uri).path).rstrip('/')
        if not path:
            continue
        labels = [label for label in graph.objects(concept, SKOS.prefLabel) if isinstance(label, Literal)]
        nl = next((str(x) for x in labels if (x.language or '').lower().startswith('nl')), None)
        fallback = str(labels[0]) if labels else path.rsplit('/', 1)[-1]
        concepts[path] = {'uri': uri, 'name': nl or fallback}

if not concepts:
    raise SystemExit('No skos:Concept instances found in TTL files')

js = r'''/* ReGeNL concept feedback modal (Qualtrics). */
(() => {
  'use strict';
  const concepts = __CONCEPTS__;
  const formUrl = __FORM_URL__;
  const css = document.createElement('style');
  css.textContent = `
    .regenl-feedback { margin: 1rem 0 1.4rem; }
    .regenl-feedback button {
      display: inline-block; background: #08635e; color: #fff !important;
      border: 0; border-radius: 5px; padding: .65rem 1rem;
      font: inherit; font-weight: 600; cursor: pointer;
    }
    .regenl-feedback button:hover, .regenl-feedback button:focus-visible {
      background: #054943; text-decoration: underline;
    }
    .regenl-feedback-overlay[hidden] { display: none !important; }
    .regenl-feedback-overlay {
      position: fixed; inset: 0; z-index: 2147483640;
      background: rgba(15, 34, 29, .66);
      display: flex; align-items: center; justify-content: center;
      padding: 18px; box-sizing: border-box;
    }
    .regenl-feedback-dialog {
      background: #fff; color: #263f33; border-radius: 12px;
      box-shadow: 0 20px 65px rgba(0,0,0,.28);
      width: min(900px, 100%); height: min(90vh, 950px);
      height: min(90dvh, 950px); display: flex; flex-direction: column;
      overflow: hidden;
    }
    .regenl-feedback-dialog-header {
      padding: 12px 18px; display: flex; align-items: center;
      justify-content: space-between; gap: 12px;
      border-bottom: 1px solid #e4ebe5;
    }
    .regenl-feedback-dialog-title { font-size: 17px; font-weight: 700; margin: 0; }
    .regenl-feedback-close { border: none; background: transparent; color: #263f33;
      font-size: 28px; line-height: 1; cursor: pointer; padding: 2px 8px; }
    .regenl-feedback-frame { width: 100%; flex: 1; border: 0; background: white; }
    .regenl-feedback-fallback { padding: 7px 18px; font-size: 12px; border-top: 1px solid #e4ebe5; }
    .regenl-feedback-fallback a { color: #08635e; }
    @media (max-width: 600px) {
      .regenl-feedback-overlay { padding: 0; }
      .regenl-feedback-dialog { width: 100%; height: 100vh; height: 100dvh; border-radius: 0; }
    }
  `;
  document.head.appendChild(css);

  const overlay = document.createElement('div');
  overlay.className = 'regenl-feedback-overlay';
  overlay.hidden = true;
  overlay.innerHTML = `
    <section class="regenl-feedback-dialog" role="dialog" aria-modal="true" aria-labelledby="regenl-feedback-title">
      <div class="regenl-feedback-dialog-header">
        <h2 id="regenl-feedback-title" class="regenl-feedback-dialog-title">Wijziging voorstellen</h2>
        <button type="button" class="regenl-feedback-close" aria-label="Sluiten">&times;</button>
      </div>
      <iframe class="regenl-feedback-frame" title="ReGeNL wijzigingsverzoek" referrerpolicy="strict-origin-when-cross-origin"></iframe>
      <div class="regenl-feedback-fallback"><a href="#" target="_blank" rel="noopener noreferrer">Formulier openen in een nieuw tabblad als het hier niet wordt geladen</a></div>
    </section>`;
  document.body.appendChild(overlay);
  const frame = overlay.querySelector('iframe');
  const closeButton = overlay.querySelector('.regenl-feedback-close');
  const fallback = overlay.querySelector('.regenl-feedback-fallback a');
  let previousFocus = null;
  let oldOverflow = '';

  function closeModal() {
    if (overlay.hidden) return;
    overlay.hidden = true;
    frame.removeAttribute('src');
    document.body.style.overflow = oldOverflow;
    if (previousFocus && previousFocus.isConnected) previousFocus.focus();
  }
  function openModal(url) {
    previousFocus = document.activeElement;
    oldOverflow = document.body.style.overflow;
    fallback.href = url;
    frame.src = url;
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
    closeButton.focus();
  }
  closeButton.addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
  document.addEventListener('keydown', (e) => {
    if (overlay.hidden) return;
    if (e.key === 'Escape') { closeModal(); return; }
    if (e.key === 'Tab') {
      const focusables = [closeButton, fallback];
      if (e.shiftKey && document.activeElement === closeButton) {
        e.preventDefault(); fallback.focus();
      } else if (!e.shiftKey && document.activeElement === fallback) {
        e.preventDefault(); closeButton.focus();
      }
    }
  });

  function currentConcept() {
    const path = decodeURI(location.pathname).replace(/\/$/, '').replace(/\.html$/, '');
    return concepts[path] || null;
  }
  let scheduled = false;
  function update() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      const entry = currentConcept();
      const existing = document.querySelector('.regenl-feedback');
      if (!entry) {
        if (existing) existing.remove();
        closeModal();
        return;
      }
      const heading = document.querySelector('main h1, main h2, article h1, article h2');
      if (!heading) return;
      const url = new URL(formUrl);
      url.searchParams.set('RegPractName', entry.name);
      url.searchParams.set('RegPractURI', entry.uri);
      if (existing) {
        const button = existing.querySelector('button');
        if (button && button.dataset.feedbackUrl === url.href) return;
        existing.remove();
      }
      const wrapper = document.createElement('div');
      wrapper.className = 'regenl-feedback';
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.feedbackUrl = url.href;
      button.textContent = 'Wijziging voorstellen';
      button.setAttribute('aria-label', 'Wijziging voorstellen voor ' + entry.name);
      button.addEventListener('click', () => openModal(url.href));
      wrapper.appendChild(button);
      heading.insertAdjacentElement('afterend', wrapper);
    });
  }
  update();
  new MutationObserver(update).observe(document.body, {childList: true, subtree: true});
  window.addEventListener('popstate', update);
})();
'''
js = js.replace('__CONCEPTS__', json.dumps(concepts, ensure_ascii=False, separators=(',', ':')))
js = js.replace('__FORM_URL__', json.dumps(FORM))
(PUBLIC / SCRIPT_NAME).write_text(js, encoding='utf-8')

# Include on all generated HTML pages. The JS only shows the button for known SKOS concept paths.
# Repeated execution is harmless: an existing script reference is not duplicated.
script = '<script defer src="/regenl-vocabulary-poc/regenl-feedback.js"></script>'
modified = 0
for html_path in PUBLIC.rglob('*.html'):
    if not html_path.is_file():
        continue
    html = html_path.read_text(encoding='utf-8')
    if SCRIPT_NAME not in html and re.search(r'</body\s*>', html, flags=re.IGNORECASE):
        html = re.sub(r'</body\s*>', lambda _: script + '</body>', html, count=1, flags=re.IGNORECASE)
        html_path.write_text(html, encoding='utf-8')
        modified += 1
print(f'ReGeNL feedback: {len(concepts)} concepts mapped, script injected into {modified} HTML files.')
