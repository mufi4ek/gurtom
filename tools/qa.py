#!/usr/bin/env python3
"""QA: verify the previously-broken words and inspect the tier pools."""
import json
import os
import random
import sqlite3
from collections import Counter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
data = json.load(open(os.path.join(OUT, "gurtom_words.json"), encoding="utf-8"))
rows = data["words"]
by = {r["w"]: r for r in rows}

print("=" * 72)
print("A. REGRESSION CHECKS (words that were wrong before)")
print("=" * 72)
checks = ["ганок", "звантажити", "тенета", "нард", "стіл", "яблуко", "хлопець",
          "кіт", "молоко", "вода", "пес", "сонце", "дім", "поїзд", "смачний",
          "любий", "тут", "так", "багато"]
for w in checks:
    r = by.get(w)
    if not r:
        print(f"  {w:12s} MISSING")
        continue
    print(f"  {w:12s} d{r['difficulty']} age{r['age']:>3d} core={r['core']} "
          f"unsuit={r['unsuit']} topics={r['topics'][:3]} fl={r['flags']} "
          f"pos={r['pos']}")

print()
print("=" * 72)
print("B. EASY TIER SAMPLE (must look like words a 8-year-old knows)")
print("=" * 72)
alias_pool = [r for r in rows if not r["unsuit"] and r["age"] == 6
              and not r["proper"] and r["pos"] in ("noun", "verb", "adjective", "adverb", "phrase")]
easy = [r for r in alias_pool if r["difficulty"] == 1]
med = [r for r in alias_pool if r["difficulty"] == 2]
hard = [r for r in alias_pool if r["difficulty"] == 3]
print(f"  alias pool: {len(alias_pool)}  easy={len(easy)} med={len(med)} hard={len(hard)}")
random.seed(4)
for label, pool in (("EASY", easy), ("MEDIUM", med), ("HARD", hard)):
    sample = random.sample(pool, min(30, len(pool)))
    print(f"\n  {label}: " + ", ".join(r["w"] for r in sample))

print()
print("=" * 72)
print("C. GAME POOLS")
print("=" * 72)
pools = {
    "Alias easy (single words)": lambda r: not r["phrase"] and not r["proper"] and r["age"] == 6 and not r["unsuit"] and r["difficulty"] == 1,
    "Alias medium": lambda r: not r["phrase"] and not r["proper"] and r["age"] == 6 and not r["unsuit"] and r["difficulty"] == 2,
    "Alias hard (incl. phrases)": lambda r: r["age"] == 6 and not r["unsuit"] and r["difficulty"] == 3,
    "Crocodile (actable)": lambda r: r["actable"],
    "Who am I (animate+person)": lambda r: r["animate"] == 1 or r["person"],
    "Taboo (has 2+ relations)": lambda r: r["taboo"],
    "Kids 6+ easy": lambda r: r["kids"],
    "Word chain (single words)": lambda r: not r["phrase"] and not r["proper"] and r["pos"] in ("noun", "adjective"),
    "Idioms / phrases": lambda r: r["idiom"],
    "Places (geo proper)": lambda r: r["place"],
    "People (proper)": lambda r: r["person"],
    "Teens 12+": lambda r: r["age"] == 12,
    "Adults 18+": lambda r: r["age"] == 18,
}
for name, pred in pools.items():
    sub = [r for r in rows if pred(r)]
    d = Counter(r["difficulty"] for r in sub)
    print(f"  {name:32s} {len(sub):6d}   d1={d[1]:6d} d2={d[2]:6d} d3={d[3]:6d}")

print()
print("=" * 72)
print("D. TOPIC BALANCE (playable, age 6)")
print("=" * 72)
tc = Counter()
for r in rows:
    if r["age"] == 6 and not r["proper"] and not r["unsuit"]:
        for t in r["topics"]:
            tc[t] += 1
tot = sum(tc.values())
for t, c in tc.most_common():
    print(f"  {t:18s} {c:6d}  ({c/tot*100:.1f}%)")
untagged = sum(1 for r in rows if not r["topics"] and r["age"] == 6 and not r["proper"])
print(f"  {'(no topic)':18s} {untagged:6d}")

print()
print("=" * 72)
print("E. SQLITE SANITY")
print("=" * 72)
con = sqlite3.connect(os.path.join(OUT, "gurtom.db"))
print("  size:", round(os.path.getsize(os.path.join(OUT, "gurtom.db")) / 1e6, 2), "MB")
for q in ["SELECT COUNT(*) FROM words",
          "SELECT COUNT(*) FROM words WHERE difficulty=1 AND age=6 AND unsuit=0 AND proper=0",
          "SELECT COUNT(*) FROM words WHERE actable=1",
          "SELECT COUNT(*) FROM words WHERE taboo=1",
          "SELECT COUNT(*) FROM words WHERE def != '[]'",
          "SELECT w, difficulty, topics FROM words WHERE w IN ('дім','поїзд','стіл','ганок') ORDER BY w"]:
    print("  ", q[:70], "->", con.execute(q).fetchall()[:6])
con.close()
