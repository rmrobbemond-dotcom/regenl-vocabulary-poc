"""ReGeNL SkoHub post-build layout and bilingual photo descriptions.

Run after add_concept_photos.py and add_regenl_feedback.py:
    python3 scripts/add_regenl_layout.py public data

Reads photoPracticeDescription from the Turtle file(s) in data, then adds
one CSS/JS asset and HTML asset links. No Gatsby source modification.
"""
from pathlib import Path
from urllib.parse import unquote
import json
import re
import sys

try:
    from rdflib import Graph, Literal, RDF, URIRef
    from rdflib.namespace import SKOS
except ImportError as exc:
    raise SystemExit('Install rdflib first: python -m pip install rdflib==7.1.4') from exc

public = Path(sys.argv[1] if len(sys.argv) > 1 else 'public').resolve()
data_dir = Path(sys.argv[2] if len(sys.argv) > 2 else 'data').resolve()
if not public.is_dir() or not data_dir.is_dir():
    raise SystemExit('Usage: python scripts/add_regenl_layout.py public data')

PREDICATE = URIRef('https://regenl.org/vocabulary/metadata/photoPracticeDescription')
entries = {}
source_count = 0
for ttl in sorted(data_dir.rglob('*.ttl')):
    # The source repository may contain multiple unrelated Turtle documents.
    g = Graph()
    try:
        g.parse(ttl, format='turtle')
    except Exception as exc:
        raise SystemExit(f'Unable to parse {ttl}: {exc}') from exc
    source_count += 1
    for s in set(g.subjects(RDF.type, SKOS.Concept)):
        descriptions = {
            str(v.language): str(v)
            for v in g.objects(s, PREDICATE)
            if isinstance(v, Literal) and v.language in {'nl', 'en'}
        }
        if not descriptions:
            continue
        key = unquote(str(s).rstrip('/').split('/')[-1])
        if key in entries and entries[key] != descriptions:
            raise SystemExit(f'Conflicting descriptions for concept {key} from several TTL files')
        entries[key] = descriptions

css = r'''/* ReGeNL details v3: no overlap between definition and photo description. */
.main-block { min-width: 0 !important; overflow-x: hidden !important; }
.main-block .regenl-detail-layout { min-width: 0; }
.main-block .regenl-detail-layout > * { min-width: 0; }
.main-block .regenl-detail-layout > h1:empty { display: none !important; }
.main-block .regenl-detail-layout .conceptURI,
.main-block .regenl-detail-layout .conceptURI * {
  overflow-wrap: anywhere; word-break: break-word;
  font-size: .82rem !important; font-weight: normal !important;
  line-height: 1.35 !important;
}
.main-block .regenl-detail-layout figure.regenl-concept-photo { margin: 0 !important; max-width: 100%; }
.main-block .regenl-detail-layout figure.regenl-concept-photo img {
  display: block; width: 100% !important; height: auto !important;
  max-height: min(42vh, 390px) !important;
  object-fit: contain !important; border-radius: 8px;
}
.main-block .regenl-detail-layout figure.regenl-concept-photo figcaption {
  font-size: .78rem; line-height: 1.4; overflow-wrap: anywhere; margin-top: .45rem;
}
.regenl-photo-description { line-height: 1.5; overflow-wrap: anywhere; }
.regenl-photo-description h2 {
  font-size: 1rem !important; line-height: 1.3; margin: 0 0 .5rem !important;
  color: #005b52;
}
.regenl-photo-description p { margin: 0; font-size: .94rem; }
.main-block .regenl-detail-layout > .markdown { min-width: 0; overflow-wrap: anywhere; }
.main-block .regenl-detail-layout > .markdown a { overflow-wrap: anywhere; }
@media (min-width: 801px) {
  .main-block .regenl-detail-layout {
    display: grid !important;
    grid-template-columns: minmax(0, 48%) minmax(0, 1fr);
    column-gap: 1.5rem; row-gap: 1rem;
    align-items: start; padding-right: .6rem;
  }
  .main-block .regenl-detail-layout > h1:not(:empty) {
    grid-column: 1 / -1; grid-row: 1; margin: 0 0 .25rem !important;
  }
  .main-block .regenl-detail-layout > figure.regenl-concept-photo {
    grid-column: 1; grid-row: 2 / span 2;
  }
  /* Force these into separate rows, overriding older layout rules. */
  .main-block > div.regenl-detail-layout > .markdown {
    grid-column: 2 !important;
    grid-row: 2 !important;
    align-self: start !important;
    position: static !important;
    margin: 0 !important;
  }
  .main-block > div.regenl-detail-layout > .regenl-photo-description {
    grid-column: 2 !important;
    grid-row: 3 !important;
    align-self: start !important;
    position: static !important;
    border-top: 1px solid rgba(0,0,0,.12);
    padding-top: .9rem;
    margin: 0 !important;
  }
  .main-block .regenl-detail-layout > .regenl-feedback {
    grid-column: 1; grid-row: 4; margin: 0 !important;
  }
  .main-block .regenl-detail-layout > .conceptURI {
    grid-column: 1 / -1; grid-row: 6; margin: .5rem 0 0;
  }
  .main-block .regenl-detail-layout > .json-png {
    grid-column: 1; grid-row: 5;
  }
}
@media (max-width: 800px) {
  .main-block .regenl-detail-layout {
    display: flex !important; flex-direction: column; gap: 1rem;
  }
  .main-block .regenl-detail-layout > h1:not(:empty) { order: 0; margin: 0 !important; }
  .main-block .regenl-detail-layout > figure.regenl-concept-photo { order: 1; }
  .main-block .regenl-detail-layout > .markdown { order: 2; }
  .main-block .regenl-detail-layout > .regenl-photo-description { order: 3; }
  .main-block .regenl-detail-layout > .regenl-feedback { order: 4; }
  .main-block .regenl-detail-layout > .conceptURI { order: 5; }
  .main-block .regenl-detail-layout > .json-png { order: 6; }
}
'''

# Keep descriptions in a local JS asset, so clients need no extra HTTP API.
# HTML pages use a relative path, which is compatible with GitHub Pages /repo/ prefixes.
js = r'''/* ReGeNL bilingual descriptions, sourced from the deployed Turtle. */
(function () {
  "use strict";
  const descriptions = __REGENL_DATA__;
  const header = { nl: 'Op de foto', en: 'In the photograph' };

  function conceptId() {
    let file = location.pathname.split('/').pop() || '';
    if (!file.endsWith('.html')) return '';
    try { return decodeURIComponent(file.slice(0, -5)); }
    catch (_) { return file.slice(0, -5); }
  }

  function selectedLanguage(container) {
    // SkoHub's <html lang> can lag behind the visible nl/en toggle.
    const markdown = container.querySelector(':scope > .markdown');
    const txt = markdown ? markdown.textContent : '';
    if (/\bDefinitie\b/.test(txt)) return 'nl';
    if (/\bDefinition\b/.test(txt)) return 'en';
    return document.documentElement.lang.toLowerCase().startsWith('nl') ? 'nl' : 'en';
  }

  function update() {
    const figure = document.querySelector('.main-block figure.regenl-concept-photo');
    if (!figure) return;
    const container = figure.parentElement;
    if (!container) return;
    container.classList.add('regenl-detail-layout');
    const id = conceptId();
    const description = descriptions[id];
    const old = container.querySelector(':scope > .regenl-photo-description');
    if (!description || (!description.nl && !description.en)) {
      if (old) old.remove();
      return;
    }
    const language = selectedLanguage(container);
    const value = description[language] || description.nl || description.en;
    if (!value) return;
    const box = old || document.createElement('section');
    const signature = id + '|' + language + '|' + value;
    if (box.dataset.regenlSignature === signature) return;
    box.className = 'regenl-photo-description';
    box.dataset.regenlSignature = signature;
    box.setAttribute('aria-label', header[language]);
    const heading = document.createElement('h2');
    heading.textContent = header[language];
    const paragraph = document.createElement('p');
    paragraph.textContent = value; // Text, not HTML: no content injection.
    box.replaceChildren(heading, paragraph);
    if (!old) container.appendChild(box);
  }

  let queued = false;
  function scheduleUpdate() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; update(); });
  }
  function start() {
    update();
    // Gatsby changes concept/language content without a full page refresh.
    const observer = new MutationObserver(scheduleUpdate);
    observer.observe(document.body, { subtree: true, childList: true, characterData: true });
    window.addEventListener('popstate', scheduleUpdate);
    document.addEventListener('click', function (e) {
      if (e.target.closest('a, button')) scheduleUpdate();
    }, true);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else { start(); }
})();
'''.replace('__REGENL_DATA__', json.dumps(entries, ensure_ascii=False, separators=(',', ':')))

(public / 'regenl-layout.css').write_text(css, encoding='utf-8')
(public / 'regenl-layout.js').write_text(js, encoding='utf-8')

# Remove our previous style injection and add links to the generated assets.
count = 0
for path in public.rglob('*.html'):
    if not path.is_file():
        continue  # Gatsby has a directory public/page-data/404.html/
    html = path.read_text(encoding='utf-8')
    html = re.sub(r'<style\s+data-regenl-layout="v1">.*?</style>', '', html, flags=re.S)
    html = re.sub(r'<link\s+data-regenl-layout-v2[^>]*>', '', html, flags=re.I)
    html = re.sub(r'<script\s+data-regenl-layout-v2[^>]*>\s*</script>', '', html, flags=re.I)
    relative = ('../' * (len(path.relative_to(public).parts) - 1))
    tags = (f'<link data-regenl-layout-v2 rel="stylesheet" href="{relative}regenl-layout.css">'
            f'<script data-regenl-layout-v2 defer src="{relative}regenl-layout.js"></script>')
    if re.search('</head>', html, re.I):
        html = re.sub('</head>', lambda _: tags + '</head>', html, count=1, flags=re.I)
        path.write_text(html, encoding='utf-8')
        count += 1

print(f'ReGeNL layout v3: {len(entries)} concepts with bilingual photo descriptions from {source_count} TTL file(s).')
print(f'Layout assets linked from {count} HTML pages.')
