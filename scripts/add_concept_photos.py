"""Add photo support to a SkoHub Pages build without forking SkoHub.

Usage: python scripts/add_concept_photos.py [public_dir] [source_data_dir]
Requires rdflib. Reads foaf:depiction from all non-generated .ttl files.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from rdflib import Graph, Namespace, URIRef

FOAF = Namespace('http://xmlns.com/foaf/0.1/')
DCTERMS = Namespace('http://purl.org/dc/terms/')
SCHEMA = Namespace('https://schema.org/')

public = Path(sys.argv[1] if len(sys.argv) > 1 else 'public')
data = Path(sys.argv[2] if len(sys.argv) > 2 else 'data')
assert public.is_dir(), f'Not found: {public}'
assert data.is_dir(), f'Not found: {data}'

entries = {}
for ttl in sorted(data.rglob('*.ttl')):
    if 'public' in ttl.parts or 'node_modules' in ttl.parts:
        continue
    graph = Graph()
    graph.parse(ttl, format='turtle')
    for concept, photo in graph.subject_objects(FOAF.depiction):
        if not isinstance(concept, URIRef) or not isinstance(photo, URIRef):
            continue
        if urlsplit(str(photo)).scheme != 'https':
            continue
        def first(prop):
            return next((str(v) for v in graph.objects(concept, prop)), '')
        entries[str(concept)] = {
            'image': str(photo),
            'source': first(DCTERMS.source),
            'credit': first(SCHEMA.creditText),
        }

(public / 'regenl-photos.json').write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding='utf-8')
js = Path(__file__).with_name('regenl-photos.js').read_text(encoding='utf-8')
(public / 'regenl-photos.js').write_text(js, encoding='utf-8')

# Inject the same script into generated HTML pages. The script handles Gatsby navigation.
repo = 'regenl-vocabulary-poc'
script = f'<script defer src="/{repo}/regenl-photos.js"></script>'
modified = 0
for html_path in public.rglob('*.html'):
    if not html_path.is_file():
    continue
    content = html_path.read_text(encoding='utf-8')
    if 'regenl-photos.js' not in content and '</body>' in content.lower():
        content = re.sub(r'</body\s*>', script + '</body>', content, count=1, flags=re.IGNORECASE)
        html_path.write_text(content, encoding='utf-8')
        modified += 1

print(f'Found {len(entries)} concepts with depictions; injected script into {modified} HTML pages.')
if not entries:
    print('WARNING: no foaf:depiction properties found; no photos will display.')
