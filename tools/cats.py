#!/usr/bin/env python3
"""Parse MediaWiki SQL dumps (page / linktarget / categorylinks) into
   page_title -> [category_title] map.

Loads each dump fully into memory (they are small: <= 55 MB uncompressed).
"""
from __future__ import annotations

import gzip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\",
           "'": "'", '"': '"', "Z": "\x1a"}


def sql_rows(path: str):
    """Yield value-lists for every tuple of every INSERT statement in the dump.

    mysqldump --extended-insert produces one huge statement per table; we scan
    the whole buffer once per statement and move the cursor past its ';'.
    """
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        data = f.read()

    n = len(data)
    cursor = 0
    while cursor < n:
        ins = data.find("INSERT INTO", cursor)
        if ins == -1:
            return
        v = data.find("VALUES", ins)
        if v == -1:
            return
        pos = v + 6
        while pos < n:
            ch = data[pos]
            if ch == ";":            # statement finished
                pos += 1
                break
            if ch != "(":
                pos += 1
                continue
            pos += 1
            row, cur = [], []
            in_str = False
            closed = False
            while pos < n:
                c = data[pos]
                if in_str:
                    if c == "\\" and pos + 1 < n:
                        cur.append(ESCAPES.get(data[pos + 1], data[pos + 1]))
                        pos += 2
                        continue
                    if c == "'":
                        if pos + 1 < n and data[pos + 1] == "'":
                            cur.append("'")
                            pos += 2
                            continue
                        in_str = False
                        pos += 1
                        continue
                    cur.append(c)
                    pos += 1
                    continue
                if c == "'":
                    in_str = True
                elif c == ",":
                    row.append("".join(cur).strip())
                    cur = []
                elif c == ")":
                    row.append("".join(cur).strip())
                    closed = True
                    pos += 1
                    break
                else:
                    cur.append(c)
                pos += 1
            if closed:
                yield row
        cursor = pos


def unesc(s: str) -> str:
    """MediaWiki titles use _ for spaces and percent-ish escaping is not applied."""
    return s.replace("_", " ").strip()


def main():
    print("reading page.sql ...", file=sys.stderr)
    pid_title = {}
    title_pid = {}
    for r in sql_rows(os.path.join(RAW, "ukwiktionary-latest-page.sql.gz")):
        if len(r) < 3:
            continue
        try:
            pid = int(r[0])
            ns = int(r[1])
        except ValueError:
            continue
        title = unesc(r[2])
        pid_title[pid] = (ns, title)
        if ns == 0:
            title_pid.setdefault(title, pid)
    print("  pages:", len(pid_title), file=sys.stderr)

    print("reading linktarget.sql ...", file=sys.stderr)
    lt = {}
    for r in sql_rows(os.path.join(RAW, "ukwiktionary-latest-linktarget.sql.gz")):
        if len(r) < 3:
            continue
        try:
            lt_id = int(r[0])
            lt_ns = int(r[1])
        except ValueError:
            continue
        if lt_ns == 14:
            lt[lt_id] = unesc(r[2])
    print("  category targets:", len(lt), file=sys.stderr)

    print("reading categorylinks.sql ...", file=sys.stderr)
    page_cats = {}
    rows = 0
    for r in sql_rows(os.path.join(RAW, "ukwiktionary-latest-categorylinks.sql.gz")):
        if len(r) < 7:
            continue
        rows += 1
        try:
            cl_from = int(r[0])
            cl_target = int(r[6])
        except ValueError:
            continue
        cat = lt.get(cl_target)
        if cat is None:
            continue
        ent = pid_title.get(cl_from)
        if not ent or ent[0] != 0:
            continue
        page_cats.setdefault(ent[1], []).append(cat)
    print("  catlink rows:", rows, " pages with cats:", len(page_cats), file=sys.stderr)

    # de-dup + prefix-strip "Категорія:"
    clean = {}
    for t, cs in page_cats.items():
        out = []
        for c in cs:
            c = re.sub(r"^(Категорія|Category):", "", c, flags=re.I).strip()
            if c and c not in out:
                out.append(c)
        if out:
            clean[t] = out

    with open(os.path.join(OUT, "page_categories.json"), "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False)

    from collections import Counter
    cc = Counter()
    for cs in clean.values():
        for c in cs:
            cc[c] += 1
    with open(os.path.join(OUT, "categories_full.json"), "w", encoding="utf-8") as f:
        json.dump(cc.most_common(), f, ensure_ascii=False, indent=0)
    print("distinct categories:", len(cc), file=sys.stderr)
    for c, k in cc.most_common(60):
        print(f"{k:7d}  {c}", file=sys.stderr)


if __name__ == "__main__":
    main()
