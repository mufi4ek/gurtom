#!/usr/bin/env python3
"""Download uk.wiktionary dumps needed for the 'Gurtom' word bank."""
import urllib.request, os, time

UA = {"User-Agent": "GurtomResearch/0.1 (mufidev; contact dev@mufidev.local)"}
BASE = "https://dumps.wikimedia.org/ukwiktionary/latest/"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "raw")
os.makedirs(OUT, exist_ok=True)

TARGETS = [
    "ukwiktionary-latest-pages-articles.xml.bz2",
    "ukwiktionary-latest-categorylinks.sql.gz",
    "ukwiktionary-latest-all-titles-in-ns0.gz",
    "ukwiktionary-latest-page.sql.gz",
]

log = open(os.path.join(OUT, "download.log"), "a", buffering=1)

for name in TARGETS:
    url = BASE + name
    dst = os.path.join(OUT, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 1000:
        log.write("SKIP %s (%d bytes)\n" % (name, os.path.getsize(dst)))
        continue
    t0 = time.time()
    got = 0
    tmp = dst + ".part"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
        os.rename(tmp, dst)
        log.write("OK %s %.1f MB in %.0fs\n" % (name, got / 1e6, time.time() - t0))
    except Exception as e:
        log.write("FAIL %s: %s %s\n" % (name, type(e).__name__, e))

log.write("ALL DONE\n")
print(open(os.path.join(OUT, "download.log")).read()[-2000:])
