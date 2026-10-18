#!/usr/bin/env python3
"""Build per-lemma 'commonness' signals from MediaWiki SQL dumps.

Signals (all cheap, all objective):
  len      - article length in bytes (longer article = richer/more central word)
  inlinks  - how many other Wiktionary pages link to this lemma
             (basic vocabulary is cited inside definitions constantly)

Output: out/signals.json  { "lemma": [len, inlinks], ... }
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cats import sql_rows  # reuse the hardened SQL tuple tokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


def unesc(s: str) -> str:
    return s.replace("_", " ").strip()


def main():
    print("page.sql ...", file=sys.stderr)
    pid = {}            # page_id -> (ns, title, page_len)
    title_len = {}      # ns0 title -> page_len
    for r in sql_rows(os.path.join(RAW, "ukwiktionary-latest-page.sql.gz")):
        if len(r) < 10:
            continue
        try:
            p_id, ns, plen = int(r[0]), int(r[1]), int(r[9])   # r[9] = page_len (r[8] = page_latest)
        except (ValueError, IndexError):
            continue
        t = unesc(r[2])
        pid[p_id] = (ns, t)
        if ns == 0:
            title_len[t] = max(title_len.get(t, 0), plen)
    print("  pages:", len(pid), " ns0:", len(title_len), file=sys.stderr)

    print("linktarget.sql ...", file=sys.stderr)
    lt = {}             # lt_id -> ns0 title
    for r in sql_rows(os.path.join(RAW, "ukwiktionary-latest-linktarget.sql.gz")):
        if len(r) < 3:
            continue
        try:
            lt_id, lt_ns = int(r[0]), int(r[1])
        except ValueError:
            continue
        if lt_ns == 0:
            lt[lt_id] = unesc(r[2])
    print("  ns0 link targets:", len(lt), file=sys.stderr)

    print("pagelinks.sql ...", file=sys.stderr)
    inl = Counter()     # ns0 title -> number of distinct pages linking to it
    rows = 0
    for r in sql_rows(os.path.join(RAW, "ukwiktionary-latest-pagelinks.sql.gz")):
        if len(r) < 3:
            continue
        rows += 1
        try:
            pl_from, pl_target = int(r[0]), int(r[2])
        except ValueError:
            continue
        t = lt.get(pl_target)
        if t:
            inl[t] += 1
    print("  pagelink rows:", rows, " targets hit:", len(inl), file=sys.stderr)

    signals = {}
    for t, ln in title_len.items():
        signals[t] = [ln, inl.get(t, 0)]
    with open(os.path.join(OUT, "signals.json"), "w", encoding="utf-8") as f:
        json.dump(signals, f, ensure_ascii=False, separators=(",", ":"))

    print("written signals for", len(signals), "titles", file=sys.stderr)
    probe = ["кіт", "хліб", "вода", "стіл", "лікар", "собака", "час", "авран", "авізо", "бунчук"]
    for w in probe:
        print(f"   {w:10s} -> {signals.get(w)}", file=sys.stderr)


if __name__ == "__main__":
    main()
