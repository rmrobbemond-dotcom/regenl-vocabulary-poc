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
