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
