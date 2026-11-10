#!/usr/bin/env python3
"""Post-build ReGeNL detail layout for SkoHub Vocabs.

Usage: python3 scripts/add_regenl_layout.py public data
Run AFTER add_concept_photos.py and add_regenl_feedback.py.
Does not alter the TTL or SkoHub source.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import SKOS

public = Path(sys.argv[1] if len(sys.argv) > 1 else "public").resolve()
data_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "data").resolve()
if not public.is_dir() or not data_dir.is_dir():
    raise SystemExit("Usage: python3 scripts/add_regenl_layout.py public data")

META = "https://regenl.org/vocabulary/metadata/"
photo_description = URIRef(META + "photoPracticeDescription")
photo_status = URIRef(META + "photoCaptionStatus")

graph = Graph()
sources = sorted(data_dir.rglob("*.ttl"))
if not sources:
    raise SystemExit(f"No TTL files found in {data_dir}")
for file in sources:
    try:
        graph.parse(file, format="turtle")
    except Exception as exc:
        raise SystemExit(f"Invalid Turtle in {file}: {exc}") from exc

def multilingual(subject, predicate):
    return {
        str(obj.language): str(obj)
        for obj in graph.objects(subject, predicate)
        if isinstance(obj, Literal) and obj.language in ("nl", "en")
    }

concepts = list(set(graph.subjects(RDF.type, SKOS.Concept)))
concept_set = set(concepts)
data = {}
for subject in concepts:
    key = unquote(str(subject).rstrip("/").rsplit("/", 1)[-1])
    level = str(next(iter(graph.objects(subject, SKOS.notation)), ""))
    description = multilingual(subject, photo_description)
    broader = sorted(
        (str(x).rstrip("/").rsplit("/", 1)[-1] for x in graph.objects(subject, SKOS.broader) if x in concept_set)
    )
    children = sorted(
        (str(x).rstrip("/").rsplit("/", 1)[-1] for x in graph.subjects(SKOS.broader, subject) if x in concept_set)
    )
    scheme = str(next(iter(graph.objects(subject, SKOS.inScheme)), ""))
    status = str(next(iter(graph.objects(subject, photo_status)), ""))
    data[key] = {
        "uri": str(subject),
        "labels": multilingual(subject, SKOS.prefLabel),
        "definitions": multilingual(subject, SKOS.definition),
        "photoDescriptions": description,
        "level": level,
        "broader": broader,
        "children": children,
        "scheme": scheme,
        "photoStatus": status,
    }

css = r"""
/* ReGeNL detail redesign v4 — replaces previous regenl-layout.css */
.main-block {min-width:0 !important; overflow-x:hidden !important;}
.main-block .regenl-detail-layout {
  display:grid !important; grid-template-columns:minmax(0,47%) minmax(0,1fr);
  column-gap:clamp(16px,2vw,28px); row-gap:18px; align-items:start;
  padding:4px 12px 18px 0; min-width:0;
}
.main-block .regenl-detail-layout > * {min-width:0;}
.main-block .regenl-detail-layout > h1 {display:none !important;}
.main-block .regenl-detail-layout > .regenl-detail-heading {grid-column:1/-1; grid-row:1;}
.regenl-detail-heading {display:flex; flex-direction:column; gap:8px; padding-bottom:4px;}
.regenl-breadcrumb {display:flex; align-items:center; gap:7px; flex-wrap:wrap; font-size:13px; color:#617570; line-height:1.4;}
.regenl-breadcrumb a {color:#006c63 !important; text-decoration:none;}
.regenl-breadcrumb a:hover {text-decoration:underline;}
.regenl-heading-row {display:flex; align-items:flex-start; gap:12px; flex-wrap:wrap;}
.regenl-detail-heading h1 {font-size:clamp(22px,2.1vw,29px) !important; line-height:1.2; margin:0 !important; color:#005b52;}
.regenl-level {display:inline-flex; align-items:center; font-size:12px; font-weight:700; line-height:1.3; border:1px solid #bed9d3;
  border-radius:999px; padding:4px 9px; color:#006f65; background:#edf6f3; white-space:nowrap;}
.main-block .regenl-detail-layout > figure.regenl-concept-photo {grid-column:1;grid-row:2; margin:0 !important;width:100%;max-width:100%;}
.main-block .regenl-detail-layout > figure.regenl-concept-photo img {
  display:block;width:100% !important;height:auto !important;
  max-width:100% !important;max-height:min(43vh,385px) !important;
  object-fit:contain !important;object-position:center; border-radius:10px;
}
.main-block .regenl-detail-layout > figure.regenl-concept-photo figcaption {
  font-size:12px;line-height:1.45;margin-top:7px;overflow-wrap:anywhere;color:#5e706c;
}
.main-block .regenl-detail-layout > .regenl-summary {grid-column:2;grid-row:2;display:flex;flex-direction:column;gap:20px;min-width:0;}
.regenl-summary-section h2,.regenl-relations h2 {
  font-size:15px !important;font-weight:700 !important;line-height:1.35 !important;
  margin:0 0 8px !important;color:#005b52 !important;
}
.regenl-summary-section p {margin:0;font-size:15px;line-height:1.55;color:#173e39;overflow-wrap:anywhere;}
.regenl-summary-section + .regenl-summary-section {border-top:1px solid #e4eae8;padding-top:16px;}
.main-block .regenl-detail-layout > .regenl-relations {grid-column:1/-1;grid-row:3;border-top:1px solid #e4eae8;padding-top:16px;}
.regenl-relation-items {display:flex;gap:9px;flex-wrap:wrap;}
.regenl-relation-link {display:inline-flex;gap:7px;align-items:center;border:1px solid #dce8e4;border-radius:8px;
  padding:9px 11px;text-decoration:none !important;color:#00645b !important;background:#f6faf8;font-size:14px;line-height:1.35;}
.regenl-relation-link:hover {background:#eaf5f1;}
.regenl-relation-group {margin-top:13px;}
.regenl-relation-group h3 {font-size:13px !important;color:#667974 !important;margin:0 0 7px !important;font-weight:600;}
.main-block .regenl-detail-layout > .regenl-feedback {grid-column:1/-1;grid-row:4;margin:0 !important;}
.main-block .regenl-detail-layout > .regenl-technical {grid-column:1/-1;grid-row:5;border-top:1px solid #e4eae8;padding-top:13px;}
.regenl-technical button {appearance:none;background:transparent;border:0;padding:4px 0;font-size:13px;
  color:#006f65;text-decoration:underline;cursor:pointer;font:inherit;}
.regenl-technical .regenl-uri {margin-top:8px;font-size:12px;color:#5f726d;overflow-wrap:anywhere;}
.regenl-technical .regenl-uri button {margin-left:8px;}
.regenl-technical .regenl-tech-note {font-size:12px;color:#5f726d;}
.main-block .regenl-detail-layout > .markdown {grid-column:1/-1;grid-row:6;display:none !important;
  min-width:0;max-width:100%;overflow-wrap:anywhere;}
.main-block .regenl-detail-layout.regenl-show-raw > .markdown {display:block !important;}
.main-block .regenl-detail-layout > .conceptURI {display:none !important;}
.main-block .regenl-detail-layout > .json-png {grid-column:1/-1;grid-row:7;}
/* Hide an obsolete injected v3 caption if left over by a legacy script */
.main-block .regenl-detail-layout > .regenl-photo-description {display:none !important;}
@media(max-width:900px) {
  .main-block .regenl-detail-layout {grid-template-columns:minmax(0,1fr);row-gap:15px;padding-right:4px;}
  .main-block .regenl-detail-layout > .regenl-detail-heading {grid-column:1;grid-row:1;}
  .main-block .regenl-detail-layout > figure.regenl-concept-photo {grid-column:1;grid-row:2;}
  .main-block .regenl-detail-layout > .regenl-summary {grid-column:1;grid-row:3;}
  .main-block .regenl-detail-layout > .regenl-relations {grid-column:1;grid-row:4;}
  .main-block .regenl-detail-layout > .regenl-feedback {grid-column:1;grid-row:5;}
  .main-block .regenl-detail-layout > .regenl-technical {grid-column:1;grid-row:6;}
  .main-block .regenl-detail-layout > .markdown {grid-column:1;grid-row:7;}
  .main-block .regenl-detail-layout > .json-png {grid-column:1;grid-row:8;}
}
"""

js_template = r"""/* ReGeNL detail redesign v4. Data comes from the site's own Turtle. */
(function () {
  'use strict';
  const concepts = __REGENL_CONCEPT_DATA__;
  const words = {
    nl: {definition:'Definitie', photo:'Op de foto', parent:'Bovenliggende begrippen',
      children:'Onderliggende praktijken', relations:'Plaats in de classificatie',
      technical:'Technische gegevens', close:'Technische gegevens verbergen', uri:'Permanente URI',
      copy:'Kopieer URI', scheme:'Vocabulaire'},
    en: {definition:'Definition', photo:'In the photograph', parent:'Broader concepts',
      children:'Narrower practices', relations:'Position in the classification',
      technical:'Technical details', close:'Hide technical details', uri:'Permanent URI',
      copy:'Copy URI', scheme:'Vocabulary'}
  };
  const rootSelector = '.main-block';
  function conceptId() {
    const file = location.pathname.split('/').pop() || '';
    try {return decodeURIComponent(file.replace(/\.html$/i,''));}
    catch (_) {return file.replace(/\.html$/i,'');}
  }
  function language(container, concept) {
    // Compare the SkoHub-rendered title against the actual TTL labels.
    // <html lang> is not a reliable indicator in SkoHub's Gatsby pages.
    const title = container.querySelector(':scope > h1:not(:empty)');
    const visible = (title && title.textContent || '').trim().toLowerCase();
    const tidy = x => (x || '').toLowerCase().replace(/\s+/g,' ').trim();
    const nl = tidy(concept.labels.nl);
    const en = tidy(concept.labels.en);
    if (nl && visible.includes(nl) && !(en && visible.includes(en))) return 'nl';
    if (en && visible.includes(en) && !(nl && visible.includes(nl))) return 'en';
    // Inspect only SkoHub content, excluding any generated sections.
    const md = container.querySelector(':scope > .markdown');
    if (md) {
      const t = md.textContent || '';
      if (/\bDefinitie\b/i.test(t) && !/\bDefinition\b/i.test(t)) return 'nl';
      if (/\bDefinition\b/i.test(t) && !/\bDefinitie\b/i.test(t)) return 'en';
    }
    const active = [...document.querySelectorAll('a,button')].find(el => {
      const label = tidy(el.textContent);
      return (label === 'nl' || label === 'en') &&
        (el.getAttribute('aria-current') === 'true' || el.getAttribute('aria-pressed') === 'true' ||
        el.getAttribute('aria-selected') === 'true');
    });
    if (active) return tidy(active.textContent);
    return (document.documentElement.lang || '').toLowerCase().startsWith('nl') ? 'nl' : 'en';
  }
  function node(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function anchor(id, locale, fallback) {
    const c = concepts[id];
    const title = (c && (c.labels[locale] || c.labels.nl || c.labels.en)) || fallback || id;
    const a = node('a','regenl-relation-link',title);
    a.href = id + '.html'; // same directory /regenl-practices/
    return a;
  }
  function section(title, body) {
    const s = node('section','regenl-summary-section');
    s.append(node('h2','',title), node('p','',body));
    return s;
  }
  function create(container, id, locale) {
    const c = concepts[id], w = words[locale];
    const heading = node('header','regenl-detail-heading');
    const crumb = node('nav','regenl-breadcrumb');
    crumb.setAttribute('aria-label',locale==='nl'?'Kruimelpad':'Breadcrumb');
    if (c.broader.length) {
      c.broader.forEach((p,i) => {
        if (i) crumb.append(node('span','','·'));
        crumb.append(anchor(p,locale));
      });
    } else {
      crumb.append(node('span','',locale==='nl'?'Regeneratieve landbouwpraktijken':'Regenerative farming practices'));
    }
    const titleRow = node('div','regenl-heading-row');
    const displayTitle = c.labels[locale] || c.labels.nl || c.labels.en || id;
    titleRow.append(node('h1','',displayTitle));
    if (c.level) titleRow.append(node('span','regenl-level',c.level));
    heading.append(crumb,titleRow);

    const summary = node('aside','regenl-summary');
    const definition = c.definitions[locale] || c.definitions.nl || c.definitions.en;
    if (definition) summary.append(section(w.definition,definition));
    const figure = container.querySelector(':scope > figure.regenl-concept-photo');
    const description = c.photoDescriptions[locale] || c.photoDescriptions.nl || c.photoDescriptions.en;
    if (figure && description) summary.append(section(w.photo,description));

    const relations = node('section','regenl-relations');
    relations.append(node('h2','',w.relations));
    const addGroup = (name,ids) => {
      if (!ids.length) return;
      const group=node('div','regenl-relation-group');
      group.append(node('h3','',name));
      const links=node('div','regenl-relation-items');
      ids.forEach(x=>links.append(anchor(x,locale)));
      group.append(links);
      relations.append(group);
    };
    addGroup(w.parent,c.broader);
    addGroup(w.children,c.children);
    if (!c.broader.length && !c.children.length) relations.hidden=true;

    const technical = node('section','regenl-technical');
    const toggle = node('button','regenl-tech-toggle',w.technical);
    toggle.type = 'button';
    toggle.setAttribute('aria-expanded','false');
    toggle.addEventListener('click',function() {
      const expanded=container.classList.toggle('regenl-show-raw');
      toggle.textContent=expanded?w.close:w.technical;
      toggle.setAttribute('aria-expanded',String(expanded));
    });
    const meta=node('div','regenl-uri');
    meta.append(node('span','',w.uri+': '+c.uri));
    const copy=node('button','',w.copy);
    copy.type='button';
    copy.addEventListener('click',()=> {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(c.uri);
    });
    meta.append(copy);
    technical.append(toggle,meta);
    if (c.scheme) {
      const scheme=node('div','regenl-tech-note');
      scheme.append(node('span','',w.scheme+': '));
      const a=node('a','',c.scheme);
      a.href=c.scheme;
      scheme.append(a);
      technical.append(scheme);
    }
    return {heading,summary,relations,technical};
  }
  function update() {
    const id=conceptId(), c=concepts[id];
    if (!c) return;
    const main=document.querySelector(rootSelector);
    if (!main) return;
    const figure=main.querySelector('figure.regenl-concept-photo');
    // The photo-injection step runs before this one. Concepts without photos
    // are still handled via the SkoHub detail container.
    const original=main.querySelector('div.main-block') || main.querySelector('div[id^="https://"]');
    const container=(figure && figure.parentElement) || original;
    if (!container || !container.querySelector(':scope > .markdown')) return;
    const locale=language(container,c);
    const signature=id+'|'+locale;
    container.classList.add('regenl-detail-layout');
    if (container.dataset.regenlRendered===signature) return;
    container.querySelectorAll(':scope > .regenl-detail-heading, :scope > .regenl-summary, :scope > .regenl-relations, :scope > .regenl-technical').forEach(x=>x.remove());
    const blocks=create(container,id,locale);
    container.append(blocks.heading,blocks.summary,blocks.relations,blocks.technical);
    container.dataset.regenlRendered=signature;
  }
  let queued=false;
  function schedule() {
    if (queued) return;
    queued=true;
    requestAnimationFrame(()=>{queued=false;update();});
  }
  function boot() {
    update();
    const observer=new MutationObserver(schedule);
    observer.observe(document.body,{childList:true,subtree:true,characterData:true});
    window.addEventListener('popstate',schedule);
    window.addEventListener('pageshow',schedule);
    document.addEventListener('click',e=>{
      if (e.target.closest('a,button')) schedule();
    },true);
  }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
"""
js = js_template.replace("__REGENL_CONCEPT_DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))

(public / "regenl-layout.css").write_text(css, encoding="utf-8")
(public / "regenl-layout.js").write_text(js, encoding="utf-8")

count = 0
for path in public.rglob("*.html"):
    if not path.is_file():
        continue  # Gatsby also has directories called 404.html.
    html = path.read_text(encoding="utf-8")
    # Rebuild from scratch on every workflow run; don't stack old styles.
    html = re.sub(r'<style\s+data-regenl-layout="v1">.*?</style>', "", html, flags=re.S|re.I)
    html = re.sub(r'<link\s+data-regenl-layout-v2[^>]*>', "", html, flags=re.I)
    html = re.sub(r'<script\s+data-regenl-layout-v2[^>]*>\s*</script>', "", html, flags=re.I)
    relative="../" * (len(path.relative_to(public).parts)-1)
    tags=(f'<link data-regenl-layout-v2 rel="stylesheet" href="{relative}regenl-layout.css">'
          f'<script data-regenl-layout-v2 defer src="{relative}regenl-layout.js"></script>')
    if re.search(r"</head>",html,re.I):
        html=re.sub(r"</head>",lambda m:tags+m.group(0),html,count=1,flags=re.I)
        path.write_text(html,encoding="utf-8")
        count+=1

print(f"ReGeNL layout v4: {len(data)} SKOS concepts from {len(sources)} TTL file(s).")
print(f"Layout assets linked from {count} HTML pages.")
