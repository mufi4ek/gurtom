#!/usr/bin/env python3
"""Robust tokenizer for MediaWiki MySQL/MariaDB dump INSERT statements.

Handles quoted strings with backslash escapes, doubled quotes, NULL and numbers.
"""
import gzip
import io


def _reader(path):
    if path.endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def sql_rows(path, chunk=1 << 22):
    """Yield lists of raw string values (quotes/escapes removed) per tuple."""
    with _reader(path) as f:
        buf = ""
        in_values = False
        while True:
            data = f.read(chunk)
            if not data:
                break
            buf += data
            if not in_values:
                idx = buf.find("INSERT INTO")
                if idx == -1:
                    buf = ""
                    continue
                v = buf.find("VALUES", idx)
                if v == -1:
                    buf = buf[idx:]
                    continue
                buf = buf[v + 6:]
                in_values = True

            pos = 0
            n = len(buf)
            while pos < n:
                c = buf[pos]
                if c == "(":
                    pos += 1
                    row = []
                    cur = []
                    in_str = False
                    ok = False
                    while pos < n:
                        c = buf[pos]
                        if in_str:
                            if c == "\\":
                                if pos + 1 >= n:
                                    break
                                nxt = buf[pos + 1]
                                mapping = {"n": "\n", "t": "\t", "r": "\r", "0": "\0",
                                           "\\": "\\", "'": "'", '"': '"', "Z": "\x1a"}
                                cur.append(mapping.get(nxt, nxt))
                                pos += 2
                                continue
                            if c == "'":
                                if pos + 1 < n and buf[pos + 1] == "'":
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
                            pos += 1
                            continue
                        if c == ",":
                            row.append("".join(cur).strip())
                            cur = []
                            pos += 1
                            continue
                        if c == ")":
                            row.append("".join(cur).strip())
                            pos += 1
                            ok = True
                            break
                        pos += 1
                    if not ok:
                        # incomplete tuple at buffer end -> rewind and refill
                        break
                    yield row
                else:
                    pos += 1
            buf = buf[pos:] if pos < n else ""
            if not buf:
                in_values = False
