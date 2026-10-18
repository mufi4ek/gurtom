#!/usr/bin/env python3
"""Debug helpers for the extractor."""
import bz2
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract as EX

NS = "{http://www.mediawiki.org/xml/export-0.11/}"
RAW = EX.RAW


def fetch(titles):
    want = set(titles)
    found = {}
    for _ev, el in ET.iterparse(bz2.BZ2File(os.path.join(RAW, "ukwiktionary-latest-pages-articles.xml.bz2")),
                                events=("end",)):
        if el.tag != NS + "page":
            continue
        t = el.findtext(NS + "title")
        if t in want and t not in found:
            te = el.find(".//" + NS + "text")
            found[t] = te.text if (te is not None and te.text) else ""
        el.clear()
        if len(found) == len(want):
            break
    return found


if __name__ == "__main__":
    freq = EX.load_freq()
    pc = EX.load_page_categories()
    print("freq size:", len(freq))
    print("freq sample:", list(freq.items())[:4], list(freq.items())[2000:2003])
    for w in ["лікар", "метод", "собака", "час", "гарбуз", "кіт", "дім", "вода", "хліб", "я"]:
        print("   rank", w, "=", freq.get(w))

    titles = ["лікар", "собака", "красивий", "бігти", "веселий", "дім", "кіт", "швидко", "мудрий"]
    found = fetch(titles)
    for k in titles:
        v = found.get(k)
        if not v:
            print("\n### (not found)", k)
            continue
        e = EX.parse_entry(k, v, freq, pc)
        print("\n###", k)
        if not e:
            print("   -> REJECTED")
            continue
        print("   syn:", e["syn"])
        print("   hyp:", e["hyp"])
        print("   d  :", [x[:70] for x in e["d"][:2]])
        print("   diff/rank/pos:", e["diff"], e["rank"], e["pos"], "cat:", e["cat"][:5])
