#!/usr/bin/env python3
"""Build a 'word-family frequency' table.

The OpenSubtitles frequency list contains raw word FORMS (собаки, собаку,
собаці ...), while the dictionary contains LEMMAS (собака).  A naive exact
join therefore matches only ~7% of lemmas and leaves difficulty grading blind.

Here we aggregate every frequency-list form into the lemma family it most
likely belongs to, using prefix bucketing.  Result: out/family_freq.json
{ lemma: total_family_count }.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "out")

UKR_LETTERS = set("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'")

# common inflectional suffixes we allow a form to add to a lemma stem
MAX_ENDING = 6


def load_forms():
    """{wordform: count} from the FrequencyWords file, Ukrainian-only."""
    path = os.path.join(RAW, "hermitdave_uk50k.txt")
    forms = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 2:
                continue
            w, c = parts[0].lower().strip(), parts[1]
            if not w.isdigit():
                pass
            try:
                c = int(c)
            except ValueError:
                continue
            if not (2 <= len(w) <= 30):
                continue
            if not all(ch in UKR_LETTERS for ch in w):
                continue          # drops Russian-only words like "что", "это"
            forms[w] = forms.get(w, 0) + c
    return forms


def stem_of(lemma: str) -> str:
    """Crude stem: drop a probable nominative ending (keeps >=3 chars)."""
    l = lemma.lower()
    for suf in ("ами", "ями", "ів", "їв", "ах", "ях", "ой", "ий", "ій", "ий",
                "ка", "ки", "ку", "ко", "ке", "ок", "ек", "ик", "а", "я", "о",
                "е", "у", "ю", "і", "и", "й", "ь"):
        if len(l) - len(suf) >= 3 and l.endswith(suf):
            return l[:len(l) - len(suf)]
    return l if len(l) >= 3 else l


def main():
    forms = load_forms()
    print("ukrainian forms loaded:", len(forms), file=sys.stderr)

    lemmas = []
    with open(os.path.join(OUT, "entries.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                w = json.loads(line)["w"].lower().replace("\u0301", "")
                if all(ch in UKR_LETTERS or ch in " -'" for ch in w):
                    lemmas.append(w)
    lemmas = sorted(set(lemmas))
    print("lemmas to match:", len(lemmas), file=sys.stderr)

    # bucket forms by their first 3 characters for fast prefix lookup
    buckets = defaultdict(list)
    for w, c in forms.items():
        if len(w) >= 3:
            buckets[w[:3]].append((w, c))

    family = {}
    hit_exact = hit_family = 0
    for L in lemmas:
        total = 0.0
        exact = forms.get(L, 0)
        if exact:
            hit_exact += 1
        total += exact * 1.0
        st = stem_of(L)
        # Require a >=4-char stem: a 3-char stem like "буд" (from "будка")
        # would happily swallow the whole future-tense family "буде/буду/
        # будеш/будуть" and promote a rare word to EASY.
        if len(st) < 4:
            st = L
        key = st[:3]
        cand = buckets.get(key, [])
        for w, c in cand:
            if w == L:
                continue
            if not w.startswith(st):
                continue
            extra = len(w) - len(st)
            if extra < 1 or extra > MAX_ENDING:
                continue
            total += c * 0.6          # discounted: family member, not the lemma
        if total > exact:
            hit_family += 1
        if total:
            family[L] = int(total)

    ranked = sorted(family.items(), key=lambda kv: -kv[1])
    rank = {}
    for i, (w, _c) in enumerate(ranked):
        rank[w] = i + 1

    with open(os.path.join(OUT, "family_freq.json"), "w", encoding="utf-8") as f:
        json.dump({"count": family, "rank": rank}, f, ensure_ascii=False, separators=(",", ":"))

    print(f"lemmas with exact form match : {hit_exact} ({hit_exact/len(lemmas)*100:.1f}%)", file=sys.stderr)
    print(f"lemmas with family frequency : {len(family)} ({len(family)/len(lemmas)*100:.1f}%)", file=sys.stderr)
    print("\n--- top 40 most frequent lemmas ---", file=sys.stderr)
    for w, c in ranked[:40]:
        print(f"  {w:14s} {c:10d}", file=sys.stderr)
    print("\n--- probe ---", file=sys.stderr)
    for w in ["кіт", "собака", "хліб", "вода", "стіл", "дім", "ганок", "офтальмолог",
              "астматик", "ідеалізм", "акмеїзм", "звантажити", "тенета", "яблуко",
              "молоко", "сонце", "рукa", "рука", "бігти", "смачний", "любий"]:
        print(f"  {w:14s} count={family.get(w)}  rank={rank.get(w)}", file=sys.stderr)


if __name__ == "__main__":
    main()
