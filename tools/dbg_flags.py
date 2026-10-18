#!/usr/bin/env python3
"""Inspect primary_region / flags for specific headwords."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract as EX
from debug import fetch

WORDS = sys.argv[1:] or ["яблуко", "хлопець", "стіл", "рука", "пес", "кіт", "батько"]
found = fetch(WORDS)
for w in WORDS:
    v = found.get(w)
    if not v:
        print("=" * 30, w, "-> NOT IN DUMP")
        continue
    text = "\n".join(EX.uk_sections(v))
    pr = EX.primary_region(text)
    print("=" * 30, w)
    print("  PRIMARY REGION:", pr[:600].replace("\n", " | "))
    print("  flags(primary):", EX.detect_flags(pr))
    print("  flags(all)    :", EX.detect_flags(text))
