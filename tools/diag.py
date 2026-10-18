#!/usr/bin/env python3
"""Diagnose why certain headwords are missing / mistagged."""
import bz2
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract as EX
import build_dataset as BD

NS = "{http://www.mediawiki.org/xml/export-0.11/}"
MISSING = ["дім", "поїзд", "любий", "смачний", "корів", "хата", "ніч", "день",
           "батько", "сон", "сніг", "літо", "зима", "хлопець", "дівчина", "рукa"]
FLAGGED = ["стіл", "яблуко", "кіт", "вода", "молоко", "пес", "сонце", "рука", "хліб"]
TOPICDBG = ["кіт", "вода", "молоко", "пес", "сонце", "ганок"]

want = set(MISSING) | set(FLAGGED) | set(TOPICDBG)
found = {}
for _ev, el in ET.iterparse(bz2.BZ2File(os.path.join(EX.RAW, "ukwiktionary-latest-pages-articles.xml.bz2")),
                            events=("end",)):
    if el.tag != NS + "page":
        continue
    t = el.findtext(NS + "title")
    if t in want and t not in found:
        te = el.find(".//" + NS + "text")
        found[t] = te.text if (te is not None and te.text) else ""
    el.clear()

freq = EX.load_freq()
pc = EX.load_page_categories()
parsed = {w: EX.parse_entry(w, found[w], freq, pc) for w in found}

print("=" * 70)
print("A. MISSING HEADWORDS")
print("=" * 70)
for w in MISSING:
    v = found.get(w)
    if v is None:
        print(f"  {w:12s} NOT IN DUMP (title absent)")
        continue
    segs = EX.uk_sections(v)
    form = bool(EX.FORM_RE.search("\n".join(segs))) if segs else None
    e = parsed.get(w)
    print(f"  {w:12s} len={len(v):6d} uk_segs={len(segs)} form_rej={form} parsed={'YES' if e else 'NO '}", end="")
    if e:
        print(f"  pos={e['pos']} age={e['age']} fl={e['fl']}")
    else:
        seg = (segs[0] if segs else v)[:260].replace("\n", " | ")
        print(f"\n      seg: {seg}")

print()
print("=" * 70)
print("B. FLAG FALSE POSITIVES (age/difficulty pollution)")
print("=" * 70)
for w in FLAGGED:
    e = parsed.get(w)
    if not e:
        print(f"  {w:10s} --")
        continue
    print(f"  {w:10s} flags={str(e['fl']):45s} age={e['age']}  def1={e['d'][0][:60] if e['d'] else '-'}")

print()
print("=" * 70)
print("C. TOPIC MATCHING DEBUG")
print("=" * 70)
for w in TOPICDBG:
    e = parsed.get(w)
    if not e:
        continue
    blob = " | ".join(e["cat"]) + " | " + " | ".join(e["hyp"])
    hits = []
    for tid, uk, en, pat in BD.TOPICS:
        m = re.search(pat, blob, re.I)
        if m:
            hits.append(f"{tid}<-'{m.group(0)}'")
    print(f"  {w:9s} {', '.join(hits)}")
    print(f"            blob: {blob[:200]}")
