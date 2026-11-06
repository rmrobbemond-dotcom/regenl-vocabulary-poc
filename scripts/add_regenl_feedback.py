"""Add a Qualtrics feedback link to each ReGeNL SKOS concept page.

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

js = r'''/* ReGeNL concept feedback link (Qualtrics). */
(() => {
  'use strict';
  const concepts = __CONCEPTS__;
  const formUrl = __FORM_URL__;
  const css = document.createElement('style');
  css.textContent = `
    .regenl-feedback { margin: 1rem 0 1.4rem; }
    .regenl-feedback a {
      display: inline-block; background: #08635e; color: #fff !important;
      border-radius: 5px; padding: .65rem 1rem;
      font-weight: 600; text-decoration: none !important;
    }
    .regenl-feedback a:hover, .regenl-feedback a:focus-visible {
      background: #054943; color: #fff !important;
      text-decoration: underline !important;
    }
  `;
  document.head.appendChild(css);

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
        return;
      }
      const heading = document.querySelector('main h1, main h2, article h1, article h2');
      if (!heading) return;
      const url = new URL(formUrl);
      url.searchParams.set('RegPractName', entry.name);
      url.searchParams.set('RegPractURI', entry.uri);
      if (existing) {
        const link = existing.querySelector('a');
        if (link && link.href === url.href) return;
        existing.remove();
      }
      const wrapper = document.createElement('div');
      wrapper.className = 'regenl-feedback';
      const link = document.createElement('a');
      link.href = url.href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'Wijziging voorstellen';
      link.setAttribute('aria-label', 'Wijziging voorstellen voor ' + entry.name + ' (opent in nieuw tabblad)');
      wrapper.appendChild(link);
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
