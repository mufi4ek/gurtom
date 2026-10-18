#!/usr/bin/env python3
"""
Gurtom ("Together") - Ukrainian word-bank extractor.
=====================================================

Builds the game dictionary for a party-games app from public dumps of
uk.wiktionary.org, enriched with a frequency list.

Sources (both freely licensed, safe to ship in an app with attribution):
  * https://dumps.wikimedia.org/ukwiktionary/  - text under CC BY-SA 3.0
  * hermitdave/FrequencyWords (OpenSubtitles)  - frequency ranks

Outputs (in ./out):
  entries.jsonl   - one JSON object per Ukrainian lemma
  stats.json      - QA statistics
  categories.json - category frequency (used to build the topic map)

Run:
  python3 cats.py        # once - builds out/page_categories.json
  python3 extract.py     # full run
  python3 extract.py 500 # smoke test on first 500 entries
"""
from __future__ import annotations

import bz2
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

XML_DUMP = os.path.join(RAW, "ukwiktionary-latest-pages-articles.xml.bz2")
NS = "{http://www.mediawiki.org/xml/export-0.11/}"

CYR = "а-яіїєґ'."          # allowed word characters (lowercase, Ukrainian)
CYR_CHAR_RE = re.compile(r"[а-яіїєґА-ЯІЇЄҐ]")
EN_OK = "[A-Za-z][A-Za-z' .-]{0,38}"

# ---------------------------------------------------------------------------
# wikitext primitives
# ---------------------------------------------------------------------------

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", re.S)
HTMLTAG_RE = re.compile(r"<[^>]{1,80}>")
MEDIA_RE = re.compile(r"\[\[\s*(?:File|Файл|Image|Зображення|Медіа)\s*:[^\]]*\]\]", re.I)
TABLE_RE = re.compile(r"\{\|.*?^\|\}", re.S | re.M)


def find_matching(text: str, start: int) -> int:
    """Return the index just past the '}}' closing the '{{' found at `start`."""
    depth, i, n = 0, start, len(text)
    while i < n:
        if text.startswith("{{", i):
            depth += 1
            i += 2
            continue
        if text.startswith("}}", i):
            depth -= 1
            i += 2
            if depth <= 0:
                return i
            continue
        i += 1
    return n


def iter_templates(text: str):
    """Yield (name_lower, full_source) for every top-level template."""
    i, n = 0, len(text)
    while i < n:
        j = text.find("{{", i)
        if j == -1:
            return
        end = find_matching(text, j)
        src = text[j:end]
        name = re.split(r"[|}]", src[2:], 1)[0].strip().lower()
        yield name, src
        i = end


def split_template_args(src: str) -> list[str]:
    """Split '{{name|a|b=c}}' into ['name','a','b=c'], nesting-aware."""
    inner = src.strip()
    if inner.startswith("{{"):
        inner = inner[2:]
    if inner.endswith("}}"):
        inner = inner[:-2]
    args, cur = [], []
    db = dk = dp = 0
    i, n = 0, len(inner)
    while i < n:
        if inner.startswith("{{", i):
            db += 1
            cur.append("{{")
            i += 2
            continue
        if inner.startswith("}}", i):
            db -= 1
            cur.append("}}")
            i += 2
            continue
        c = inner[i]
        if c == "[":
            dk += 1
        elif c == "]":
            dk -= 1
        elif c == "(":
            dp += 1
        elif c == ")":
            dp -= 1
        if c == "|" and db <= 0 and dk <= 0 and dp <= 0:
            args.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    args.append("".join(cur))
    return [a.strip() for a in args]


STYLE_LABELS = {
    "перен", "розм", "заст", "жарт", "рідк", "діал", "урочист", "спец", "зневажл",
    "лайл", "вульг", "іст", "політ", "реліг", "рел", "анат", "бот", "зоол", "мед",
    "юр", "військ", "тех", "хім", "спорт", "муз", "кулінар", "інформ", "комп",
    "поет", "ірон", "груб", "неолог", "архіт", "авіа", "мат", "ем", "фіз", "астр",
    "геол", "біол", "лінгв", "грам", "текст", "філос", "збірн", "мор", "книжн",
    "офіц", "побут", "образн", "терм", "сленг", "жарг", "проф", "етногр", "фольк",
    "міфол", "церк", "бібл", "істор", "прав", "економ", "фін", "торг", "сільгосп",
    "буд", "археол", "геогр", "метеор", "кіно", "театр", "літ", "іл", "ілюстрац",
    "розмов", "діалект", "неценз", "жартівл", "іроніч", "поетичн", "урочисте",
    "застаріле", "рідкісне", "переносне", "спеціальне", "матем", "філософ",
}

DROP_TPL_RE = re.compile(
    r"^(приклад2?|семантика|позначка|виділ|джерело|color swatch|cf|омоніми|ulif|ds\d*|"
    r"wikipedia1?|довжина слова|списки семантичних зв.?язків|multilang|ілюстрац|іл|"
    r"(?:синоніми|антоніми|гіпероніми|гіпоніми|холоніми|мероніми|гіперо-гіпонімічна|"
    r"меронімічна|холонімічна)\s*[:\w\s-]*|"
    r"(?:імен|ім|дієсл|прикм|присл|займ|числ|прийм|сполуч|частк|вигук|дієприкм|"
    r"дієприсл|предик|phrase|морфо|transcription|audio|транскрипція|t-uk|t-ru|склади|"
    r"переклад|категорія|форма|іменник|прислівник|прикметник|дієслово|займенник|"
    r"числівник|прийменник|сполучник|інфінітив|значення|word|lang|PAGENAME)\b.*|"
    r"t|to|m|f|n|c|іст|перен|розм|заст|жарт|рідк|діал|урочист|спец|зневажл|лайл|"
    r"вульг|політ|реліг|рел|анат|бот|зоол|мед|юр|військ|тех|хім|спорт|муз|кулінар|"
    r"інформ|комп|архіт|авіа|мат|ем|фіз|астр|геол|біол|лінгв|грам|поет|ірон|образно|"
    r"сленг|жарг|груб|неолог|тип|стан|ч|р|база|мова|-[а-яіїєґ']{1,6}|[\w]{2,14}\.)$",
    re.I,
)



def strip_templates(text: str) -> str:
    """Remove known-noise templates; keep the visible text of the rest."""
    res, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("{{", i):
            end = find_matching(text, i)
            src = text[i:end]
            name = re.split(r"[|}]", src[2:], 1)[0].strip()
            # {{перен.|uk}}, {{філос.|uk}}, {{мор.|uk}} - domain labels end with '.'
            if name.endswith(".") or name.lower().rstrip(".") in STYLE_LABELS:
                i = end
                continue
            if not DROP_TPL_RE.match(name):
                res.append(re.sub(r"\{\{|\}\}", " ", src))
            i = end
            continue
        res.append(text[i])
        i += 1
    return "".join(res)


def wiki_to_plain(text: str) -> str:
    """Convert a wikitext fragment to clean plain text."""
    if not text:
        return ""
    t = COMMENT_RE.sub(" ", text)
    t = REF_RE.sub(" ", t)
    t = MEDIA_RE.sub(" ", t)
    t = TABLE_RE.sub(" ", t)
    t = strip_templates(t)
    t = HTMLTAG_RE.sub(" ", t)

    def _link(m):
        inner = m.group(1)
        if inner.lower().startswith(("file:", "файл:", "image:", "категорія:", "category:")):
            return " "
        if re.match(r"^[a-z\-]{2,12}:", inner):        # interwiki [[pl:слово]]
            return " "
        return inner.split("|")[-1]

    t = re.sub(r"\[\[([^\[\]]*)\]\]", _link, t)
    t = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", t)
    t = t.replace("'''", "").replace("''", "")
    t = html.unescape(t)
    t = t.replace("\u00a0", " ").replace("\u2013", "-").replace("\u2014", "-")
    t = re.sub(r"[*#:;]+", " ", t)
    t = re.sub(r"\{\{|\}\}|\|", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" \t-,.:;()[]{}|/'\"\u0301")


LINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")


def collect_linked(text: str) -> list[str]:
    out = []
    for m in LINK_RE.finditer(text or ""):
        v = m.group(1).split("|")[-1]
        if v and not re.match(r"^(File|Файл|Image|Категорія|Category):", v, re.I):
            out.append(v)
    return out


STYLE_PREFIX_RE = re.compile(
    r"^(?:перен|розм|заст|жарт|рідк|діал|урочист|спец|зневажл|лайл|вульг|іст|політ|"
    r"реліг|рел|анат|бот|зоол|мед|юр|військ|тех|хім|спорт|муз|кулінар|інформ|комп|поет|"
    r"ірон|груб|неолог|архіт|авіа|мат|ем|фіз|астр|геол|біол|лінгв|грам|текст|філос|"
    r"збірн|мор|книжн|офіц|побут|образно|терм|сленг|жарг|проф|етногр|фольк|міфол|"
    r"церк|бібл|істор|прав|економ|фін|торг|сільгосп|буд|археол|геогр|метеор|кіно|"
    r"театр|літ|розмов|діалект|неценз|жартівл|іроніч|поетичн|матем|філософ|"
    r"застаріле|рідкісне|переносне|спеціальне|урочисте)\s*\.\s*(?:uk\s*)?",
    re.I,
)
BALANCED_PAREN_RE = re.compile(r"\([^()]{0,40}\)")


BAD_ITEM_RE = re.compile(r"[{}\[\]|=<>*#]")


def tidy_item(c: str) -> str:
    """Normalise one extracted string: drop style markers and stray brackets."""
    if not c:
        return ""
    c = re.sub(r"\s+", " ", c).strip()
    prev = None
    while prev != c:                       # strip repeated markers: "перен. розм."
        prev = c
        c = STYLE_PREFIX_RE.sub("", c).strip()
    c = BALANCED_PAREN_RE.sub("", c)       # drop complete parentheticals
    if c.count("(") != c.count(")"):       # unbalanced -> cut at the stray bracket
        c = re.split(r"[(\[]", c, 1)[0]
    c = re.sub(r"\s+", " ", c).strip(" .;,:-()[]‖")
    return c


JUNK_ITEMS = {
    "\u2014", "-", "\u2013", "", "немає", "нема", "none",
    "заст", "застаріле", "розм", "розмовне", "перен", "переносне",
    "жарт", "жартівливе", "рідк", "рідкісне", "діал", "діалектне",
    "урочист", "урочисте", "спец", "спеціальне", "зневажл", "зневажливе",
    "лайл", "лайливе", "вульг", "вульгарне", "іст", "історичне",
    "політ", "реліг", "анат", "бот", "зоол", "мед", "юр", "військ",
    "тех", "образно", "у порівняннях", "грубо", "нецензурне",
}


def split_list_items(text: str) -> list[str]:
    """Turn a wiki list / comma-separated chunk into clean item strings."""
    if not text:
        return []
    text = COMMENT_RE.sub(" ", text)
    parts = re.split(r"(?:^|\n)\s*[*#:]+\s*|[,;]|\|", text)
    out = []
    for p in parts:
        candidates = [wiki_to_plain(p)] + [wiki_to_plain(x) for x in collect_linked(p)]
        for cand in candidates:
            c = tidy_item(cand)
            if not c or len(c) < 2 or len(c) > 70:
                continue
            if BAD_ITEM_RE.search(c):
                continue
            if re.search(r"\d{3,}", c):
                continue
            if c.lower().strip(" .") in JUNK_ITEMS:
                continue
            out.append(c)
            break
    return list(dict.fromkeys(out))


HEADING_RE = re.compile(r"^(={2,7})\s*(.+?)\s*\1\s*$", re.M)


def get_sections(text: str, title_re: str, stop_at_deeper: bool = False) -> list[str]:
    """Bodies of every section whose heading matches `title_re`.

    stop_at_deeper=True also stops at sub-headings (needed for list sections
    such as 'Усталені словосполучення', which are followed by empty
    '==== Колокації ====' stubs we must not swallow).
    """
    heads = [(m.start(), m.end(), len(m.group(1)), m.group(2))
             for m in HEADING_RE.finditer(text)]
    bodies = []
    for idx, (_s, e, lvl, title) in enumerate(heads):
        if not re.search(title_re, title, re.I):
            continue
        end = len(text)
        for s2, _e2, lvl2, _t2 in heads[idx + 1:]:
            if lvl2 < lvl or (stop_at_deeper and lvl2 <= lvl + 1):
                end = s2
                break
        bodies.append(text[e:end])
    return bodies


LANG_MARK_RE = re.compile(
    r"(?:^\s*=\s*\{\{-\s*([a-zA-Z\-]+)\s*-\}\}\s*=\s*$)|(?:^\s*\{\{=\s*([a-zA-Z\-]+)\s*=)",
    re.M,
)
UK_TPL_RE = re.compile(
    r"\{\{\s*(?:імен|дієсл|прикм|присл|займ|числ|прийм|сполуч|частк|вигук|phrase|Форма-)",
    re.I,
)


def uk_sections(text: str) -> list[str]:
    """Slice the article into per-language segments, return only Ukrainian ones."""
    marks = [(m.start(), m.end(), (m.group(1) or m.group(2) or "").lower())
             for m in LANG_MARK_RE.finditer(text)]
    if not marks:
        return [text] if UK_TPL_RE.search(text) else []
    segs = []
    for i, (_s, e, lang) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        if lang == "uk":
            segs.append(text[e:end])
    if not segs:
        head = text[:marks[0][0]]
        if UK_TPL_RE.search(head):
            segs.append(head)
    return segs


# ---------------------------------------------------------------------------
# linguistic maps
# ---------------------------------------------------------------------------

POS_TPL = [
    ("phrase", r"^(phrase|фразеологізм|ідіома)"),
    ("participle", r"^дієприкм"),
    ("gerund", r"^дієприсл"),
    ("noun", r"^ім\b|^імен\b|^noun"),
    ("verb", r"^дієсл\b|^verb"),
    ("adjective", r"^прикм\b|^adj"),
    ("adverb", r"^присл\b|^adv"),
    ("pronoun", r"^(займ|займенник)"),
    ("numeral", r"^(числ|числівник)"),
    ("preposition", r"^(прийм|прийменник)"),
    ("conjunction", r"^(сполуч|сполучник)"),
    ("particle", r"^(частк|частка)"),
    ("interjection", r"^(вигук|interj)"),
    ("predicative", r"^(предик|предикатив)"),
]

POS_TEXT = [
    ("phrase", r"фразеологізм|ідіома|усталене словосполучення"),
    ("participle", r"дієприкметник"),
    ("gerund", r"дієприслівник"),
    ("noun", r"іменник"),
    ("verb", r"дієслово"),
    ("adjective", r"прикметник"),
    ("adverb", r"прислівник"),
    ("pronoun", r"займенник"),
    ("numeral", r"числівник"),
    ("preposition", r"прийменник"),
    ("conjunction", r"сполучник"),
    ("particle", r"\bчастка\b"),
    ("interjection", r"вигук"),
    ("predicative", r"предикатив"),
]

POS_FROM_CAT = [
    ("participle", r"дієприкметники?$"),
    ("gerund", r"дієприслівники?$"),
    ("noun", r"іменники?$"),
    ("verb", r"дієслова?$"),
    ("adjective", r"прикметники?$"),
    ("adverb", r"прислівники?$"),
    ("pronoun", r"займенники?$"),
    ("numeral", r"числівники?$"),
    ("preposition", r"прийменники?$"),
    ("conjunction", r"сполучники?$"),
    ("particle", r"частки?$"),
    ("interjection", r"вигуки?$"),
    ("phrase", r"фразеологізми?$|прислів.?я$"),
]

GENDER_FROM_CAT = [("m", r"Чоловічий рід"), ("f", r"Жіночий рід"), ("n", r"Середній рід")]

FLAG_TPL = {
    "archaic": r"заст|архаїзм|староукр",
    "archaic2": r"^іст$",
    "colloquial": r"розм|побут",
    "slang": r"сленг|жарг",
    "vulgar": r"лайл|неценз|вульг|^груб$|обсцен",
    "dialect": r"діал|говор|гуцул|лемк",
    "figurative": r"перен|образно|метафор",
    "humorous": r"жарт|ірон",
    "solemn": r"урочист|поет",
    "pejorative": r"зневажл|образл",
    "technical": r"^спец$|термін|техн",
    "political": r"політ",
    "religious": r"реліг|церк|бібл",
    "anatomy": r"анат|фізіол",
    "biology": r"^бот$|^зоол$|біол",
    "military": r"військ|воєн",
    "legal": r"^юр$|правн",
    "medical": r"^мед$|клініч",
    "rare": r"рідк|неолог",
    "chemistry": r"^хім$",
    "sports": r"^спорт$",
    "music": r"^муз$|музич",
    "culinary": r"кулінар|гастр",
    "it": r"інформ|комп|інтернет",
}
FLAG_ALIASES = {"archaic2": "archaic"}

FORM_RE = re.compile(
    r"\{\{\s*Форма-|\bform of\b|\bформа\s+(?:родового|давального|знахідного|"
    r"орудного|місцевого|називного|кличного)\s+відмінка",
    re.I,
)

CATEG_TPL_RE = re.compile(r"\{\{\s*Категорія\s*\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}", re.I)
CATLINK_RE = re.compile(r"\[\[\s*(?:Категорія|Category)\s*:\s*([^\]|]+)", re.I)

DEF_HEAD = r"^=?\s*Значення"
SYN_HEAD = r"^=?\s*Синоніми"
ANT_HEAD = r"^=?\s*Антоніми"
HYP_HEAD = r"^=?\s*Гіпероніми"
HYPO_HEAD = r"^=?\s*Гіпоніми"
HOL_HEAD = r"^=?\s*Холоніми"
MER_HEAD = r"^=?\s*Мероніми"
PHR_HEAD = r"Усталені|словосполучення|фразеологіз"
PROV_HEAD = r"Прислів.я та приказки"
MORPH_HEAD = r"Морфосинтаксичні ознаки|Тип та синтаксичні ознаки"

PROPER_CAT_RE = re.compile(r"власн|прізвищ|топонім|псевдонім|кличк|назви", re.I)

CAT_NOISE_RE = re.compile(
    r"^(Сторінки|Потрібна|Потрібно|Потрібен|Немає відомостей|Належить|Шаблони|"
    r"Вікісловник|Статті|Слова з \d+ букв|Українські слова|"
    r"Співзвуччя|Омоніми|Мінімальні пари|Вікіпедія|Незавершені|Помилки|Перевірити|"
    r"Уточнити|Всі мови|Мови|Індекси|Списки|Додаток|Категорія|Множина|Однина|"
    r"Головна|Озвучені|Чергування голосних|Болванки|Цитати|Перехідні дієслова|"
    r"Недоконаний вид|Доконаний вид|Переносні вирази|Стійкі словосполуки|"
    r"Усталені словосполучення|Предметні слова|Українські лексеми|Українська мова|"
    r"Істоти|Неістоти|Чоловічий рід|Жіночий рід|Середній рід|Singularia|Pluralia)",
    re.I,
)

# etymology buckets ("Грецизми", "Праслов'янізми", "Англізми") - not game topics
ETYMOLOGY_CAT_RE = re.compile(r"(?:ізми|изми|ізмами|запозичен|субстрат)$", re.I)

# grammatical categories of OTHER languages, e.g. "Кримськотатарські іменники"
FOREIGN_GRAMMAR_CAT_RE = re.compile(
    r"^(?!Українськ)(?:[А-ЯІЇЄҐ][\w'’\-]{2,24})\s*"
    r"(?:мова|мови|мові|мовний|лексеме?и?|іменники?|дієслова?|прикметники?|"
    r"прислівники?|займенники?|числівники?|прийменники?|сполучники?|частки?|вигуки?|"
    r"фразеологізми?|прислів'?я|топоніми?|прізвища?|імена|абревіатури|літери|"
    r"іменникові|дієслівні)$",
    re.I,
)


FOREIGN_CAT_RE = re.compile(
    r"/(?:ru|be|pl|en|de|fr|es|it|pt|nl|sv|fi|cs|sk|bg|sr|mk|hr|sl|hu|ro|el|tr|"
    r"ja|zh|ko|vi|id|he|ar|hi|fa|la|eo|et|lv|lt|da|no|is|ga|cy|ka|hy|az|kk|ky|uz|"
    r"tk|tt|ba|cv|psl|orv|cu|chu|io|ia|art|grc|sa|ta|th|my|km|lo|mo|sh|tl|ms|ur|bn)$",
    re.I,
)

# categories that describe ANOTHER language section of the same wiki page
LANG_NAME_CAT_RE = re.compile(
    r"^(російськ|російська|білоруськ|польськ|українсько-|болгарськ|македонськ|сербськ|"
    r"хорватськ|боснійськ|словенськ|чеськ|словацьк|лужицьк|кашубськ|англійськ|англійська|"
    r"німецьк|німецька|нідерландськ|французьк|французька|іспанськ|іспанська|італійськ|"
    r"португальськ|румунськ|молдовськ|угорськ|фінськ|шведськ|норвезьк|данськ|ісландськ|"
    r"естонськ|латиськ|латвійськ|литовськ|грецьк|латинськ|турецьк|арабськ|перськ|іврит|"
    r"єврейськ|китайськ|японськ|корейськ|в'єтнамськ|тайськ|лаоськ|кхмерськ|бірманськ|"
    r"індонезійськ|малайськ|філіппінськ|тагальськ|хілі|індійськ|хінді|урду|бенгальськ|"
    r"тамільськ|грузинськ|вірменськ|азербайджанськ|казахськ|киргизськ|узбецьк|туркменськ|"
    r"таджицьк|татарськ|башкирськ|чуваськ|монгольськ|бурятськ|якутськ|тибетськ|непальськ|"
    r"африкаанс|суахілі|есперанто|інтерлінгва|волапюк|ід|ложебан|клінгон|синдарин|"
    r"праслов'янськ|прасловянськ|церковнослов'янськ|церковнослов'янська|староцерковно|"
    r"давньоруськ|давньоукраїнськ|санскрит|єгипетськ|шумерськ|аккадськ|етруськ|"
    r"інші мови|всі мови|мови\s)",
    re.I,
)

# grammatical/inflectional categories - no value for gameplay
CAT_MORPH_NOISE_RE = re.compile(
    r"відмінювання|парадигма|морфемної будови|з суфіксом|з префіксом|словозміна|"
    r"наголос|Сingularia|Pluralia|Singularia tantum|Pluralium tantum|тип відмінювання|"
    r"істоти/|неістоти/|Чоловічий рід|Жіночий рід|Середній рід|Істоти|Неістоти|"
    r"лексем|Синонімічні вирази|германізми|англізми|латинізми|галліцизми|русизми|"
    r"полонізми|тюркізми|запозичен",
    re.I,
)


# content that must never reach players, even in 18+ mode
HARD_BLOCK_RE = re.compile(
    r"\b(хуй|ху[еє]т|пизд|єб[ау]|ебать|їбат|сука|бляд|блять|мудак|гандон|гондон|"
    r"дроч|залуп|шлюх|повія|проститут|педик|підор|срака|срач|говн|дерьм|минет|"
    r"оргазм|порно|секс|єбл|трахат|клітор|вагін|сперм|генітал|екстаз|презерватив)",
    re.I,
)
SOFT_ADULT_RE = re.compile(
    r"\b(алкогол|горілк|вино|пиво|тютюн|цигарк|наркот|збро|війн|вбивст|смерт|"
    r"кров|труп|еротик|голи|роздяг|цілувати|обійми|кохан|флірт|п'ян|"
    r"раб\b|рабств|рабин|кріпак|кріпац|насиль|ґвалт|самогуб|повішан|"
    r"тортур|катув|страт|ув'язн|в'язниц|тюрм|наркоман|алкоголік|"
    r"жебр|безпритульн|проститу|повія|сутенер|азартн|казино|ставк)",
    re.I,
)


def clean_categories(cats):
    """Drop noise / other-language categories; derive gender, animacy and POS."""
    kept, gender, animacy, gram_pos = [], "", -1, None   # animacy: -1 ?, 1 жива, 0 нежива
    for c in cats:
        c = re.sub(r"^(Категорія|Category):", "", c, flags=re.I).strip()
        if not c or len(c) > 60:
            continue
        if FOREIGN_CAT_RE.search(c):            # belongs to another language section
            continue
        base = re.sub(r"(?:/[a-z\-]{2,5})+$", "", c).strip()   # "Хімія/uk/uk" -> "Хімія"
        for g, pat in GENDER_FROM_CAT:
            if re.search(pat, base, re.I):
                gender = g
        low = base.lower()
        if low == "істоти":
            animacy = 1
        elif low == "неістоти":
            animacy = 0
        if gram_pos is None and base.lower().startswith("українськ"):
            for pos, pat in POS_FROM_CAT:
                if re.search(pat, base, re.I):
                    gram_pos = pos
                    break
        if (LANG_NAME_CAT_RE.match(base) or CAT_MORPH_NOISE_RE.search(base)
                or CAT_NOISE_RE.match(base) or ETYMOLOGY_CAT_RE.search(base)
                or FOREIGN_GRAMMAR_CAT_RE.match(base)):
            continue
        # grammatical class is a POS hint, never a gameplay topic
        if re.match(r"^Українські (іменники|дієслова|прикметники|прислівники|"
                    r"займенники|числівники|прийменники|сполучники|частки|вигуки|"
                    r"фразеологізми)", base, re.I):
            continue
        if base not in kept:
            kept.append(base)
    return kept, gender, animacy, gram_pos



def semantyka_field(src: str, field: str) -> str:
    for a in split_template_args(src)[1:]:
        if a.lower().startswith(field + "="):
            return a.split("=", 1)[1]
    return ""


def detect_pos(text: str, gram_pos: str | None) -> str:
    for name, _src in iter_templates(text):
        if re.fullmatch(r"-[" + CYR.replace("'.", "") + r"]{1,5}", name):
            return "noun"                       # suffix templates: {{-ння}}, {{-ість}}
        for pos, pat in POS_TPL:
            if re.match(pat, name):
                return pos
    if gram_pos:                                # from "Українські іменники" etc.
        return gram_pos
    morph = get_sections(text, MORPH_HEAD, stop_at_deeper=True)
    probe = wiki_to_plain(" ".join(morph) if morph else text[:1500])
    for pos, pat in POS_TEXT:
        if re.search(pat, probe, re.I):
            return pos
    if re.search(r"морфо-uk\|[^}]*\+ти\b", text):
        return "verb"
    return "other"


def detect_flags(text: str) -> list:
    flags = set()

    def test(raw_name):
        nm = raw_name.strip(".").lower()
        for flag, pat in FLAG_TPL.items():
            plain = pat.replace(r"^", "").replace(r"$", "")
            if re.fullmatch(plain, nm) or re.search(r"\b" + plain + r"\b", nm):
                flags.add(FLAG_ALIASES.get(flag, flag))

    for name, src in iter_templates(text):
        test(name)
        for m in re.finditer(r"\{\{\s*([а-яіїєґa-z]{2,14})\s*\.", src, re.I):
            test(m.group(1))
    for m in re.finditer(r"\{\{\s*([а-яіїєґa-z]{2,14})\s*(?:\.[^|]*)?\|", text, re.I):
        test(m.group(1))
    return sorted(flags)


def primary_region(text: str) -> str:
    """Morphology + FIRST definition only.

    Secondary senses pollute the entry: 'стіл' has a specialised geological
    sense, 'яблуко' an archaic 'potato' sense, 'хлопець' a historical one.
    Age rating and difficulty must follow the primary sense.
    """
    morph = get_sections(text, MORPH_HEAD, stop_at_deeper=True)
    defs = get_sections(text, DEF_HEAD, stop_at_deeper=True)
    first = ""
    for body in defs:
        for line in body.split("\n"):
            ls = line.strip()
            if re.match(r"^#{1,5}\s*\S", ls):
                first = ls
                break
        if first:
            break
    return " ".join(morph) + "\n" + first



COMBINING_ACCENT_RE = re.compile(r"[\u0300\u0301\u0302\u0306]")

VERB_END_RE = re.compile(r"(?:ти|ть|чи|тися|тись|тиcь)$", re.I)
ADJ_END_RE = re.compile(r"(?:ий|ій|ої|ова|ове|ові|їний|їна|їне)$", re.I)


def strip_accents(s: str) -> str:
    return COMBINING_ACCENT_RE.sub("", s)


def guess_pos(lemma: str) -> str:
    """Infer POS from the headword ending (used for stub articles only)."""
    tail = strip_accents(lemma.split()[-1]).lower().rstrip(".")
    if VERB_END_RE.search(tail):
        return "verb"
    if ADJ_END_RE.search(tail):
        return "adjective"
    return "noun"


def stub_definitions(text: str, lemma: str) -> list:
    """Stub ('болванка') articles keep the definition in the leading paragraph.

    Structure:  {{=uk=}}\\n'''Метод''' - [[шлях]], [[спосіб]] ...\\n=== Джерела ===
    """
    head = re.split(r"^={2,7}", text, maxsplit=1, flags=re.M)[0]
    plain = strip_accents(wiki_to_plain(head)).strip()
    if not plain:
        return []
    lem = strip_accents(lemma).lower()
    if plain.lower().startswith(lem):
        plain = plain[len(lem):]
    plain = plain.lstrip(" -\u2013\u2014:,.()").strip()
    if len(plain) < 8:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[А-ЯІЇЄҐA-Z])", plain)
    out = []
    for p in parts:
        p = p.strip(" .;,:-")
        if len(p) >= 8:
            out.append(p)
    return out[:6]


REL_BAD_START_RE = re.compile(
    r"^(а|і|й|та|що|як|або|чи|але|проте|бо|щоб|якщо|це|той|та|те|ті|який|яка|яке|"
    r"у|в|він|вона|воно|вони|на|до|від|з|зі|із|при|для|о|об|над|під|перед|після|"
    r"серед|між|без|через|завдяки|окрім|крім|також|зокрема|навіть|дуже|тільки|"
    r"ним|ним|його|її|їх|ми|ви|ти|я|собі|себе|хто|що|чого|тому|так|ні|не|де|коли)\b",
    re.I,
)


def relation_ok(v: str) -> bool:
    """A synonym/hyperonym must look like a short lexical unit, not prose."""
    if not (2 <= len(v) <= 28):
        return False
    if len(v.split()) > 3:
        return False
    if re.search(r"[«»\"0-9;:!?.]", v):
        return False
    if not re.fullmatch(r"[\w'’\- ]+", v):
        return False
    if REL_BAD_START_RE.match(v):
        return False
    return True


def parse_entry(title, wikitext, freq, page_cats):
    lemma = title.replace("_", " ").strip()
    if not (2 <= len(lemma) <= 60):
        return None
    if "\ufffd" in lemma or "\ufffd" in (wikitext or "")[:2000]:
        return None                                   # corrupt encoding in dump
    if lemma.startswith(("-", "\u2013", "\u2014")):
        return None                                   # morpheme entry ("-енк", "-изм")
    if "\u00ab" in lemma or "\u00bb" in lemma or '"' in lemma:
        return None                                   # quoted proper name
    if re.search(r"[0-9@#$%^&*_+=/\\<>{}\[\]|~`(\u2026\u00b7\u2022]", lemma):
        return None
    n_cyr = len(CYR_CHAR_RE.findall(lemma))
    if n_cyr < 2:
        return None                                   # "р.", "й", single letters
    if " " not in lemma and n_cyr < 3:
        return None

    segs = uk_sections(wikitext)
    if not segs:
        return None
    text = "\n".join(segs)
    if FORM_RE.search(text):
        return None                             # inflected form, not a lemma

    raw_cats = []
    for m in CATEG_TPL_RE.finditer(text):
        for a in m.group(1).split("|")[1:]:
            a = wiki_to_plain(a)
            if a:
                raw_cats.append(a)
    for m in CATLINK_RE.finditer(text):
        c = wiki_to_plain(m.group(1))
        if c:
            raw_cats.append(c)
    raw_cats.extend(page_cats.get(lemma, []))
    cats, gender, animacy, gram_pos = clean_categories(list(dict.fromkeys(raw_cats)))

    pos = detect_pos(text, gram_pos)
    flags_all = detect_flags(text)
    flags = detect_flags(primary_region(text))     # primary sense drives age/difficulty

    words = [w for w in lemma.split() if w]
    n_words = len(words)
    is_phrase = n_words >= 2 or pos == "phrase"

    definitions = []
    for body in get_sections(text, DEF_HEAD, stop_at_deeper=True):
        for line in body.split("\n"):
            ls = line.strip()
            if not re.match(r"^#{1,5}\s*\S", ls):
                continue
            d = tidy_item(wiki_to_plain(re.sub(r"^#{1,5}\s*", "", ls)))
            d = d.strip(" .;,:-")
            # a definition must actually contain Cyrillic prose, not just "-"
            if (d and len(d) > 3 and len(CYR_CHAR_RE.findall(d)) >= 3
                    and d not in definitions):
                definitions.append(d)

    inferred_pos = False
    if not definitions:                       # stub article - no "Значення" section
        definitions = stub_definitions(text, lemma)
    if pos == "other" and definitions:
        pos = guess_pos(lemma)
        inferred_pos = True

    def gather(head_re, field):
        vals = []
        for body in get_sections(text, head_re, stop_at_deeper=True):
            vals.extend(split_list_items(body))
        for _n, src in iter_templates(text):
            if re.match(r"семантика", src[2:].strip(), re.I):
                v = semantyka_field(src, field)
                if v:
                    vals.extend(split_list_items(v))
        return [v for v in dict.fromkeys(vals) if v != lemma and relation_ok(v)]

    synonyms = gather(SYN_HEAD, "синоніми")
    antonyms = gather(ANT_HEAD, "антоніми")
    hypernyms = gather(HYP_HEAD, "гіпероніми")
    hyponyms = gather(HYPO_HEAD, "гіпоніми")
    holonyms = gather(HOL_HEAD, "холоніми")
    meronyms = gather(MER_HEAD, "мероніми")

    phrases = []
    for head in (PHR_HEAD, PROV_HEAD):
        for body in get_sections(text, head, stop_at_deeper=True):
            phrases.extend(split_list_items(body))
    phrases = [p for p in dict.fromkeys(phrases)
               if 3 < len(p) < 90 and p != lemma and len(p.split()) >= 2]

    en = []
    for name, src in iter_templates(text):
        if not re.match(r"переклад", name):
            continue
        for a in split_template_args(src)[1:]:
            if not a.lower().startswith("en="):
                continue
            v = a.split("=", 1)[1]
            en.extend(re.findall(r"\{\{\s*(?:t|to)\s*\|\s*en\s*\|\s*([^|}]+)", v))
            en.extend(collect_linked(v))
            plain = wiki_to_plain(v)
            if plain:
                en.append(plain)
    en = [e.strip() for e in dict.fromkeys(en)
          if e and re.fullmatch(EN_OK, e.strip())]

    proper = bool(lemma[0].isupper()) or any(PROPER_CAT_RE.search(c) for c in cats)

    # ---------------- difficulty -----------------------------------------
    key = lemma.replace("\u0301", "").lower()
    rank = freq.get(key) or freq.get(key.replace("'", ""))
    if rank is None and not is_phrase:
        for w in words:
            r = freq.get(w.lower())
            if r:
                rank = r
                break

    score = 0.0
    if rank is None:
        score += 1.6
    elif rank <= 1500:
        score -= 1.2
    elif rank <= 5000:
        score -= 0.4
    elif rank <= 15000:
        score += 0.4
    elif rank <= 35000:
        score += 1.2
    else:
        score += 1.6

    score += {2: 1.0, 3: 1.5, 4: 2.0}.get(n_words, 2.4 if n_words > 4 else 0.0)

    HARD_FLAGS = ("archaic", "technical", "rare", "dialect", "legal", "medical",
                  "military", "religious", "chemistry", "it", "political")
    score += 0.45 * sum(1 for f in HARD_FLAGS if f in flags)
    if "colloquial" in flags:
        score -= 0.4
    if len(lemma) > 15:
        score += 0.3
    if synonyms or hypernyms:
        score -= 0.3
    if pos in ("noun", "verb") and n_words == 1 and 3 <= len(lemma) <= 11:
        score -= 0.3
    if proper:
        score += 0.6

    difficulty = 1 if score < 0.8 else (2 if score < 2.2 else 3)

    # ---------------- age rating ------------------------------------------
    age = 6
    if any(f in flags for f in HARD_FLAGS):
        age = 12
    if any(f in flags for f in ("slang", "pejorative")):
        age = max(age, 12)
    if pos in ("pronoun", "preposition", "conjunction", "particle", "numeral"):
        age = max(age, 12)
    if "vulgar" in flags:
        age = 18
    blob = lemma + " " + " ".join(definitions[:2])
    if SOFT_ADULT_RE.search(blob):
        age = max(age, 12)
    if HARD_BLOCK_RE.search(blob):
        age = 18
    blocked = bool(re.search(HARD_BLOCK_RE, blob))

    return {
        "w": lemma,
        "pos": pos,
        "ph": 1 if is_phrase else 0,
        "nw": n_words,
        "proper": 1 if proper else 0,
        "gen": gender,
        "anim": animacy,
        "d": definitions[:6],
        "syn": synonyms[:12],
        "ant": antonyms[:8],
        "hyp": hypernyms[:8],
        "hypo": hyponyms[:10],
        "hol": holonyms[:6],
        "mer": meronyms[:8],
        "phr": phrases[:12],
        "en": en[:6],
        "cat": cats[:16],
        "fl": flags,
        "fla": flags_all,
        "ipos": 1 if inferred_pos else 0,
        "diff": difficulty,
        "age": age,
        "blocked": 1 if blocked else 0,
        "rank": rank or 0,
        "len": len(lemma),
    }


def load_freq() -> dict:
    path = os.path.join(RAW, "hermitdave_uk50k.txt")
    freq = {}
    if not os.path.exists(path):
        return freq
    word_re = re.compile(r"^[" + CYR + r"a-z\s-]+$")
    with open(path, encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            parts = line.split()
            if len(parts) < 2:
                continue
            w = parts[0].lower().strip()
            if word_re.match(w):
                freq.setdefault(w, i + 1)
    return freq


def load_page_categories() -> dict:
    p = os.path.join(OUT, "page_categories.json")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main(limit=None):
    freq = load_freq()
    page_cats = load_page_categories()
    print(f"freq entries: {len(freq)}  pages with categories: {len(page_cats)}", file=sys.stderr)

    n_pages = n_ns0 = n_out = n_err = 0
    cat_counter, pos_counter, diff_counter, age_counter, flag_counter = (Counter() for _ in range(5))
    coverage = Counter()
    entries, errs = [], []

    for _ev, el in ET.iterparse(bz2.BZ2File(XML_DUMP), events=("end",)):
        if el.tag != NS + "page":
            continue
        n_pages += 1
        if el.findtext(NS + "ns") != "0":
            el.clear()
            continue
        n_ns0 += 1
        title = (el.findtext(NS + "title") or "").strip()
        te = el.find(".//" + NS + "text")
        wikitext = te.text if (te is not None and te.text) else ""
        el.clear()
        if not wikitext:
            continue
        try:
            e = parse_entry(title, wikitext, freq, page_cats)
        except Exception as exc:
            n_err += 1
            if len(errs) < 30:
                errs.append(f"{title}: {type(exc).__name__} {exc}")
            continue
        if not e:
            continue
        n_out += 1
        entries.append(e)
        pos_counter[e["pos"]] += 1
        diff_counter[e["diff"]] += 1
        age_counter[e["age"]] += 1
        for f in e["fl"]:
            flag_counter[f] += 1
        for c in e["cat"]:
            cat_counter[c] += 1
        for k in ("d", "syn", "ant", "hyp", "hypo", "phr", "en", "cat"):
            if e[k]:
                coverage[k] += 1
        if n_pages % 10000 == 0:
            print(f"  ...{n_pages} pages / {n_out} uk entries", file=sys.stderr)
        if limit and n_out >= limit:
            break

    stats = {
        "pages_total": n_pages,
        "pages_ns0": n_ns0,
        "entries_uk": n_out,
        "parse_errors": n_err,
        "pos": dict(pos_counter.most_common()),
        "difficulty": {str(k): v for k, v in sorted(diff_counter.items())},
        "age": {str(k): v for k, v in sorted(age_counter.items())},
        "flags": dict(flag_counter.most_common()),
        "coverage_pct": {k: round(v / max(1, n_out) * 100, 1) for k, v in coverage.items()},
        "distinct_categories": len(cat_counter),
        "sample_errors": errs,
    }
    with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "categories.json"), "w", encoding="utf-8") as f:
        json.dump(cat_counter.most_common(), f, ensure_ascii=False, indent=0)
    with open(os.path.join(OUT, "entries.jsonl"), "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    show = {k: v for k, v in stats.items() if k not in ("sample_errors",)}
    print(json.dumps(show, ensure_ascii=False, indent=1), file=sys.stderr)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
