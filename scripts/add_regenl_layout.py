"""Apply the ReGeNL concept-detail layout to generated SkoHub HTML pages.
Run after all other HTML post-processing steps and before deploy.
No changes to the input TTL, Gatsby sources, or the existing photo/feedback scripts.
"""
from pathlib import Path
import re
import sys

public = Path(sys.argv[1] if len(sys.argv) > 1 else 'public')
if not public.is_dir():
    raise SystemExit(f'Cannot find generated public folder: {public}')

css = r'''/* ReGeNL responsive concept detail layout */
@media (min-width: 801px) {
  .main-block { min-width: 0 !important; overflow-x: hidden !important; }

  /* Select only the component rendered by SkoHub for concepts with photos. */
  .main-block > div:has(> figure.regenl-concept-photo) {
    display: grid !important;
    grid-template-columns: minmax(0, 46%) minmax(0, 1fr);
    column-gap: 1.5rem;
    row-gap: .75rem;
    align-items: start;
    min-width: 0;
    padding-right: 1.5rem;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > h1:empty {
    display: none !important;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > h1:not(:empty) {
    grid-column: 1 / -1;
    grid-row: 1;
    margin: 0 0 .25rem !important;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > figure.regenl-concept-photo {
    grid-column: 1;
    grid-row: 2;
    width: 100%;
    min-width: 0;
    max-width: 100%;
    margin: 0 !important;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > figure.regenl-concept-photo img {
    display: block;
    width: 100% !important;
    height: auto !important;
    max-width: 100% !important;
    max-height: min(44vh, 430px) !important;
    object-fit: contain !important;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > figure.regenl-concept-photo figcaption {
    font-size: .8rem;
    line-height: 1.4;
    overflow-wrap: anywhere;
    margin-top: .5rem;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > .regenl-feedback {
    grid-column: 1;
    grid-row: 3;
    margin: 0 !important;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > .markdown {
    grid-column: 2;
    grid-row: 2 / span 2;
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > .conceptURI {
    grid-column: 1 / -1;
    grid-row: 6;
    min-width: 0;
    max-width: 100%;
    overflow-wrap: anywhere;
    word-break: break-word;
    margin: 1rem 0 0;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > .conceptURI,
  .main-block > div:has(> figure.regenl-concept-photo) > .conceptURI * {
    font-size: .85rem !important;
    font-weight: normal !important;
    line-height: 1.35 !important;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > .json-png {
    grid-column: 1;
    grid-row: 4;
  }
  .main-block > div:has(> figure.regenl-concept-photo) > * {
    min-width: 0;
  }
}
@media (max-width: 800px) {
  .main-block { overflow-x: hidden !important; }
  .main-block figure.regenl-concept-photo {
    max-width: 100% !important;
  }
  .main-block figure.regenl-concept-photo img {
    width: 100% !important;
    height: auto !important;
    max-height: 38vh !important;
    object-fit: contain !important;
  }
  .main-block .conceptURI, .main-block .conceptURI * {
    overflow-wrap: anywhere;
    word-break: break-word;
  }
}
'''
marker = 'data-regenl-layout="v1"'
block = f'<style {marker}>\n{css}\n</style>'
count = 0
for path in public.rglob('*.html'):
    if not path.is_file():
    continue
    html = path.read_text(encoding='utf-8')
    # Remove older versions of the same injected style (safe for reruns).
    html = re.sub(r'<style\s+data-regenl-layout="v1">.*?</style>', '', html, flags=re.S)
    if re.search(r'</head\s*>', html, flags=re.I):
        html = re.sub(r'</head\s*>', lambda _: block + '\n</head>', html, count=1, flags=re.I)
        path.write_text(html, encoding='utf-8')
        count += 1
print(f'ReGeNL layout stylesheet added to {count} generated HTML pages.')
