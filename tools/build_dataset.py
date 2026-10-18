#!/usr/bin/env python3
"""
Gurtom / "Together" - game word bank builder.
=============================================

Turns raw Wiktionary extraction (out/entries.jsonl) into a shippable dataset:

  * recalculates difficulty from real usage signals + quantiles (so each
    difficulty tier is guaranteed to hold ~1/3 of the pool)
  * maps categories / hyperonyms onto gameplay topics
  * builds per-game pools (Alias, Crocodile, Who-am-I, Taboo, Word-chain,
    Hat, Kids) and age gates (6+ / 12+ / 18+)
  * writes SQLite + JSON + a human-readable QA report

Outputs (in ./out):
  gurtom.db            - SQLite for app assets
  gurtom_words.json    - full JSON (for inspection / web tools)
  topics.json          - topic dictionary (uk + en labels)
  pools_summary.json   - machine-readable QA stats
  REPORT.md            - human-readable QA report
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core_vocab
import party_content

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

APP_NAME_UK = "Гуртом"
APP_NAME_EN = "Together"
BRAND = "mufidev"

# ---------------------------------------------------------------------------
# topic map: (id, uk label, en label, regex over categories+hyperonyms)
# ---------------------------------------------------------------------------

TOPICS = [
    ("traits", "Ознаки та якості", "Traits & Qualities",
     r"якісний|властивості|ознака|розмір|величина|форма якості|характеристика|"
     r"кольори|колір|відтінок|швидкість|вага|довжина|висота|глибина|"
     r"позитивні оцінки|негативні оцінки|оцінки|якість"),
    ("animals", "Тварини", "Animals",
     r"тварин|ссавц|пта[хш]|риб[иа]|комаш|комахи|плазун|худоб|коні|кінь|собак|кіт |"
     r"котяч|зоолог|орнітолог|іхтіолог|собаки|гризун|комахоїд|безхребет|хижак|порода|"
     r"пташин|звірі|плазуни|амфіб|молюск|черв'як|бджіл|метелик|коняр"),
    ("plants", "Рослини й природа", "Plants & Nature",
     r"рослин|дерева|кущі|стебл|плоди|ліси|ботан|квіти|квітк|гриби|ягоди|фрукт|овочі|"
     r"трава|зілля|корен|листя|насінн|садов|городн|злаки|ягідні|горіх"),
    ("food", "Їжа та напої", "Food & Drinks",
     r"їжа|страви|продукти|харчуван|напої|хліб|кулінар|спиртн|алкогольн|м'ясні|десерт|"
     r"каші|супи|соуси|приправи|борошно|цукор|сіль|молоко|сир|м'ясо|риба як їжа|випічка|"
     r"гастроном|рідкі страви|салатні|харчов"),
    ("people", "Людина та родина", "People & Family",
     r"людина|соціальні ролі|жінки|чоловіки|діти|родинн|шлюб|сім['’]я|колективи|"
     r"національна належність|народи|вік|стать|мати|батько|подруж|родичі|хлопч|дівчат"),
    ("profession", "Професії та робота", "Jobs & Work",
     r"професі|робітники|спеціалісти|посади|робота|праця|виробництво|підприємства|"
     r"керівники|музиканти|солдати|лікарі|учител|будівельні професії|медичні професії|"
     r"творчі професії|релігійні професії|фахівці|ремесла|торгівл|агентиви"),
    ("body", "Тіло та здоров'я", "Body & Health",
     r"анатом|фізіолог|захворюван|медицин|фармац|тіло|частини тіла|органи|хвороб|ліки|"
     r"симптом|травм|гігієна|зір|слух|нюх|смак|дотик|зуб|волос|шкіра|кістк|м'яз|кров"),
    ("home", "Дім і побут", "Home & Objects",
     r"предмети побуту|меблі|посуд|контейнери|пристрої|прилади|інструмент|знаряддя|"
     r"деталі|покриття|побутова хімія|канцелярськ|предмети|речі|посудини|кімнат|"
     r"постіль|ванна|кухонн|господарськ|побут"),
    ("clothes", "Одяг і взуття", "Clothes & Shoes",
     r"одяг|взуття|головні убори|прикраси|тканини|верхній одяг|жіночий одяг|"
     r"чоловічий одяг|деталі одягу|вбранн|костюм|пальто|сукн|сорочк|штани|черевики"),
    ("transport", "Транспорт", "Transport",
     r"транспорт|автомобілі|авіаційн|морські терміни|дороги|вантаж|поїзд|автобус|"
     r"велосипед|мотоцикл|літак|корабель|човен|судно|трактор|вантажівк|таксі|метро"),
    ("buildings", "Будівлі та місця", "Buildings & Places",
     r"приміщення|споруди|будівл|установи|заклади|архітектур|будівельн|місто|"
     r"село|вулиц|площа|міст |парк|стадіон|лікарн|школ|університет|театр як будівля|"
     r"церква як будівля|вокзал|аеропорт|готель|ресторан|магазин|будинок"),
    ("geography", "Географія та подорожі", "Geography & Travel",
     r"географіч|країни|столиці|туризм|край|простір|річки|гори|море|океан|острів|"
     r"континент|пустел|озер|гідронім|водойм|клімат|сторони світу|мапа|компас"),
    ("nature_weather", "Природа та погода", "Nature & Weather",
     r"природ|погода|метеоролог|земля|вода|повітря|небо|сонце|місяць як небесне|астроном|"
     r"зірки|дощ|сніг|вітер|хмар|гроза|сезон|пори року|весн|літо|осін|зим|температур"),
    ("sport", "Спорт та ігри", "Sport & Games",
     r"спорт|спортивн|футбол|баскетбол|волейбол|хокей|теніс|бокс|плаванн|біг |гімнаст|"
     r"шахи|ігри|іграшк|лижі|ковзан|олімпій|тренуван|змаганн|командн|атлет"),
    ("art_music", "Мистецтво та музика", "Art & Music",
     r"музик|мистецтв|театр|літератур|твори|книжки|зображення|кольори|живопис|"
     r"скульптур|архітектурн|танец|танці|пісні|інструмент|худож|поетич|фільм|кіно|"
     r"актор|спів|оркестр|мелоді|ритм|нот|балет|цирк"),
    ("science_tech", "Наука й техніка", "Science & Tech",
     r"наука|техніка|фізика|хімія|математичн|біологія|комп'ютерн|інтернет|"
     r"електротехніч|енергетик|медіа|біохім|геолог|винахід|робот|програмуван|"
     r"інженер|лаборатор|дослід|електр|магніт|атом|молекул"),
    ("emotions", "Емоції та характер", "Emotions & Character",
     r"почуття|думки|емоці|характер|властивост|якість|позитивні оцінки|негативні оцінки|"
     r"погляд|настрій|радість|сум|страх|гнів|любов|ненависть|сором|гордість|вдача|"
     r"темперамент|психологіч"),
    ("actions", "Дії та рух", "Actions & Motion",
     r"^дія$|діяльніст|рух |швидкість|події|поведінка|процеси|вербальні слова|звуки|"
     r"сила|крок|стрибок|політ|падінн|удари|жест|міміка|дії |спосіб дії"),
    ("time_abstract", "Час і абстрактні поняття", "Time & Abstract",
     r"^час|місяці|величини|кількість|числа|форми|системи|матерія|явища|цілість|"
     r"розвиток|філософ|значення|інформаці|простір|початок|кінець|тривалість|"
     r"частини доби|дoba|рік|тиждень|доба|ранок|вечір|ніч|день"),
    ("society", "Суспільство та економіка", "Society & Money",
     r"суспільство|держава|влада|політик|вибори|право|юридичн|економік|фінанси|гроші|"
     r"торгівл|соціолог|громадськ|закон|суд|податк|банк|валют|монети|цін|багатство|"
     r"бідність|ринок|товар|підприємець"),
    ("war", "Війна та зброя", "War & Weapons",
     r"військ|військо|вогнепальн|зброя|солдати|захист|армія|війн|битва|оборон|атака|"
     r"снаряд|гармат|кулемет|шабл|меч |щит|броня|окоп|полк|генерал"),
    ("religion_myth", "Релігія та міфи", "Religion & Myth",
     r"релігія|церковн|християнств|міфологіч|боги|святі|ангели|демони|біблійн|молитв|"
     r"храм|монастир|піст|великдень|різдво|язичниц|обряд|ритуал|легенд"),
    ("school", "Школа та освіта", "School & Education",
     r"освіта|навчання|школа|урок|іспит|студент|учень|вчитель|зошит|підручник|олівець|"
     r"пенал|клас|диплом|університет|лекція|домашнє завдання|оцінка|буквар"),
    ("culture", "Культура та традиції", "Culture & Traditions",
     r"культура|етнограф|свята|традиці|обряди|звичаї|фольклор|народно|вишиван|"
     r"писанк|коляд|щедрівк|весіл|народні|українськ(а|і|их)? (традиц|культур)"),
    ("language", "Мова та слова", "Language & Words",
     r"^мова$|^слова$|граматик|мовознавств|лінгвістичн|фразеологія|літера|алфавіт|"
     r"речення|прикметник|іменник як термін|дієслово як термін|вимова|наголос|"
     r"переклад|словник|діалект"),
    ("farm", "Село та господарство", "Farm & Countryside",
     r"сільськогосподарськ|сільське господарство|тваринництво|город|лан|поле|жнива|"
     r"плуг|трактор|корів|конюшн|пасіка|бджоляр|садівницт|ферм|стійло|копит"),
]

TOPIC_NOISE_RE = re.compile(
    r"^(дієслова?|дієприкметник|помилка в морфемному|абревіатур|слова, відсутні|"
    r"слова відсутні|деривати|зменшено-пестливі|feminina|незмінювані|іменники "
    r"(чоловічого|жіночого|середнього|спільного)|чужомовні|реалії по факту|фірмоніми|"
    r"культуроніми|слова однини|слова, які використовуються|українські |російські |"
    r"номіна|номени|словозміна|терміни, що|багатозначні|омоніми|синоніміч|"
    r"сторінки|потрібн|нележить|належить|озвучені|чергування|болванки|цитати|"
    r"незавершен|статті|вікісловник|шаблони|індекс|списки|додаток|категорія)",
    re.I,
)

# proper-noun pools
PROPER_PEOPLE_RE = re.compile(
    r"прізвищ|ім[']?ена|чоловічі імена|жіночі імена|псевдонім|кличк|найменування жителів|"
    f"українські (чоловічі|жіночі) імена", re.I)
PROPER_PLACE_RE = re.compile(
    r"топонім|села|селища|міста|область|район|країни|столиці|річки|гідронім|вулиці|"
    r"регіон|острови|гори|місцевост", re.I)
PHRASE_RE = re.compile(
    r"фразеологія|усталені словосполучення|стійкі словосполуки|розмовні вирази|"
    r"образні вирази|прислів|приказк|збірні вирази|ідіом", re.I)
ONOMATOPOEIA_RE = re.compile(r"ономатопея|звуконаслідуван", re.I)

# topics considered concrete enough to pantomime ("Крокодил")
ACTABLE_TOPICS = {
    "animals", "plants", "food", "people", "profession", "body", "home", "clothes",
    "transport", "buildings", "sport", "art_music", "actions", "farm",
    "nature_weather", "traits",
}
# topics too abstract to act out / explain to kids
ABSTRACT_TOPICS = {"time_abstract", "language", "science_tech", "society", "emotions",
                   "religion_myth", "war"}

# content that must be excluded from the default (family) pool
SENSITIVE_CAT_RE = re.compile(r"реалії по факту|лайливі вирази|зневажливі вирази", re.I)

POS_LABEL = {
    "noun": "іменник", "verb": "дієслово", "adjective": "прикметник",
    "adverb": "прислівник", "phrase": "фразеологізм", "pronoun": "займенник",
    "numeral": "числівник", "preposition": "прийменник", "conjunction": "сполучник",
    "particle": "частка", "interjection": "вигук", "participle": "дієприкметник",
    "gerund": "дієприслівник", "predicative": "предикатив", "other": "інше",
}
PLAYABLE_POS = {"noun", "verb", "adjective", "adverb", "phrase", "participle",
                "gerund", "interjection"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _compile_topic(pat: str) -> re.Pattern:
    """Compile a topic pattern so every alternative respects a left word edge.

    Without this, 'військ' matches inside 'с-військ-ий' (кіт свійський) and
    'окоп' matches inside 'Мол-окоп-родукти'.
    """
    out = []
    for alt in pat.split("|"):
        alt = alt.strip()
        if not alt:
            continue
        if alt.startswith("^") or alt.startswith("(?"):
            out.append(alt)
        else:
            out.append(r"(?<![\w'’\-])" + alt)
    return re.compile("|".join(out), re.I)


TOPIC_RES = [(tid, uk, en, _compile_topic(pat)) for tid, uk, en, pat in TOPICS]


def match_topics(cats, hyp):
    """Topic ids matched against each category/hyperonym individually.

    Per-item matching avoids cross-boundary false hits; the returned order
    follows the canonical TOPICS order, so the first element is the primary
    topic and can be used for UI grouping.
    """
    items = [c for c in list(cats) + list(hyp) if c]
    hits = []
    for tid, _uk, _en, rx in TOPIC_RES:
        for it in items:
            if rx.search(it):
                hits.append(tid)
                break
    return hits



def percentile(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    i = min(len(sorted_vals) - 1, max(0, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[i]


def main():
    with open(os.path.join(OUT, "entries.jsonl"), encoding="utf-8") as f:
        entries = [json.loads(l) for l in f if l.strip()]
    with open(os.path.join(OUT, "signals.json"), encoding="utf-8") as f:
        signals = json.load(f)
    fam_path = os.path.join(OUT, "family_freq.json")
    fam_rank, fam_count = {}, {}
    if os.path.exists(fam_path):
        with open(fam_path, encoding="utf-8") as f:
            _fam = json.load(f)
        fam_rank, fam_count = _fam.get("rank", {}), _fam.get("count", {})
    print(f"loaded {len(entries)} entries, {len(signals)} signal rows, "
          f"{len(fam_rank)} family-frequency ranks", file=sys.stderr)

    # ---- curated core vocabulary -----------------------------------------
    CORE_MAP = core_vocab.core_map()     # word -> {age, diff, topics:[...]}
    print(f"core vocabulary: {len(CORE_MAP)} curated words", file=sys.stderr)

    known = {e["w"].lower() for e in entries}
    VERB_END = re.compile(r"(?:ти|ть|чи|тися|тись)$", re.I)
    ADJ_END = re.compile(r"(?:ий|ій|ої|ова|ове|ові)$", re.I)
    added_core = 0
    for w, rec in CORE_MAP.items():
        if w in known:
            continue
        age, diff = rec["age"], rec["diff"]
        words = w.split()
        if VERB_END.search(words[-1]):
            pos = "verb"
        elif ADJ_END.search(words[-1]):
            pos = "adjective"
        elif len(words) >= 2:
            pos = "phrase"
        else:
            pos = "noun"
        entries.append({
            "w": w, "pos": pos, "ph": 1 if len(words) >= 2 or pos == "phrase" else 0,
            "nw": len(words), "proper": 1 if w[0].isupper() else 0,
            "gen": "", "anim": -1, "d": [], "syn": [], "ant": [], "hyp": [],
            "hypo": [], "hol": [], "mer": [], "phr": [], "en": [], "cat": [],
            "fl": [], "fla": [], "ipos": 1, "diff": diff, "age": age,
            "blocked": 0, "rank": 0, "len": len(w), "_core": 1,
        })
        added_core += 1
    for e in entries:
        e.setdefault("_core", 0)
    print(f"core words inserted (absent from Wiktionary): {added_core}", file=sys.stderr)

    # ---- pass 1: usage score (how "common" a word really is) --------------
    for e in entries:
        ln, inl = signals.get(e["w"], [0, 0])
        key = e["w"].lower().replace("\u0301", "")
        frank = fam_rank.get(key) or fam_rank.get(key.replace("'", ""))
        fcount = fam_count.get(key) or fam_count.get(key.replace("'", "")) or 0
        e["_len"] = ln
        e["_inl"] = inl
        e["_frank"] = frank or 0
        e["_fcount"] = fcount
        n_defs = len(e["d"])
        # Article LENGTH measures how well Wiktionary documents a word, not how
        # often people say it - so it gets a small weight only. The subtitle
        # family frequency and the in-link count are the real signals.
        usage = 0.0
        if frank:
            usage += max(0.0, (9.0 - math.log(max(frank, 1))) * 2.20)
        usage += math.log1p(fcount) * 0.90
        usage += math.log1p(inl) * 1.35
        usage += min(n_defs, 8) * 0.45
        usage += math.log1p(ln) * 0.35
        if e["syn"]:
            usage += 0.6
        if e["hyp"]:
            usage += 0.4
        if e["en"]:
            usage += 0.4
        e["_usage"] = round(usage, 3)

    # ---- pass 2: topics --------------------------------------------------
    for e in entries:
        e["_topics"] = match_topics(e["cat"], e["hyp"])
        blob = " | ".join(e["cat"])
        e["_proper_people"] = 1 if (e["proper"] and PROPER_PEOPLE_RE.search(blob)) else 0
        e["_proper_place"] = 1 if (e["proper"] and PROPER_PLACE_RE.search(blob)) or \
                                 (PROPER_PLACE_RE.search(blob) and not e["_topics"]) else 0
        e["_idiom"] = 1 if (e["ph"] or PHRASE_RE.search(blob)) else 0
        e["_onomatopoeia"] = 1 if ONOMATOPOEIA_RE.search(blob) else 0
        e["_sensitive"] = 1 if SENSITIVE_CAT_RE.search(blob) else 0

        core = CORE_MAP.get(e["w"].lower())
        if core:
            ctopics = [t for t in core["topics"] if t != "idioms"]
            if "idioms" in core["topics"]:
                e["_idiom"] = 1
            for ct in ctopics:
                if ct not in e["_topics"]:
                    e["_topics"].append(ct)
            # curated topics are more trustworthy than parsed categories:
            # stable-sort them to the front so topics[0] is the primary one
            e["_topics"].sort(key=lambda t: ctopics.index(t) if t in ctopics else 99)
            fla = e.get("fla") or e["fl"]
            if e["age"] > core["age"] and "vulgar" not in fla and not e["_sensitive"]:
                e["age"] = core["age"]
            if e["proper"] and "geography" in core["topics"]:
                e["_proper_place"] = 1
        # sensitive content (war realities, pejorative sets) is never family-level
        if e["_sensitive"]:
            e["age"] = max(e["age"], 12)

    # ---- pass 3: rule-based difficulty ----------------------------------
    # Percentiles over a noisy continuous score produced nonsense (dialectal
    # 'звантажити' landed in EASY while everyday 'ганок' landed in HARD).
    # So: hard/soft gates first, then fill the remaining slots by usage rank
    # so each tier is still well populated.
    HARD_FLAGS_3 = ("archaic", "rare", "dialect")
    # NOTE: anatomy / biology / music / sports / culinary labels are routinely
    # attached to perfectly everyday words (рука, кіт, серце, пісня, футбол,
    # борщ), so they must NOT push a word out of the easy tier.
    HARD_FLAGS_2 = ("technical", "legal", "medical", "chemistry", "it",
                    "military", "religious", "political")

    # words that are grammatical glue - useless to explain or pantomime
    UNSUITABLE = {
        "тут", "там", "так", "ні", "не", "і", "а", "у", "в", "на", "з", "до",
        "від", "по", "за", "під", "над", "перед", "після", "через", "для",
        "про", "але", "що", "як", "коли", "де", "хто", "чому", "дуже",
        "більш", "менш", "багато", "мало", "трохи", "ще", "вже", "теж",
        "також", "лише", "тільки", "завжди", "ніколи", "іноді", "часто",
        "рідко", "ось", "он", "ну", "ото", "це", "той", "та", "те", "ті",
        "він", "вона", "воно", "вони", "ми", "ви", "ти", "я", "себе",
        "який", "яка", "яке", "які", "чий", "скільки", "якщо", "бо",
        "щоб", "хоча", "проте", "однак", "тому", "отже", "нарешті",
        "можна", "треба", "варто", "здається", "бути", "є", "був", "була",
        # inflected pronoun / particle forms that have their own wiki pages
        "вам", "нам", "ним", "ними", "нього", "нього", "ньому", "мені",
        "тобі", "йому", "їй", "їм", "їх", "нас", "вас", "них", "мною",
        "тобою", "собою", "мене", "тебе", "його", "її", "ким", "чим",
        "кого", "чого", "кому", "чому", "ким", "чім", "тім", "сім",
        "було", "були", "буде", "буду", "будеш", "будемо", "будете",
        "будуть", "маю", "маєш", "має", "маємо", "маєте", "мають",
        "можу", "можеш", "може", "можемо", "можете", "можуть",
        "немає", "нема", "немає", "хіба", "невже", "адже", "ба",
        "осьо", "о", "об", "є", "тільки-но", "саме", "тільки",
    }

    # topics concrete enough that an 8-year-old can explain or act them out;
    # the subtitle frequency list over-represents abstract "movie talk"
    # (філософія, місія, паніка), so EASY additionally requires one of these
    CONCRETE_TOPICS = {
        "animals", "plants", "food", "people", "profession", "body", "home",
        "clothes", "transport", "buildings", "sport", "art_music", "actions",
        "farm", "nature_weather", "traits", "school", "culture",
    }

    def pool_key(e):
        if e["_proper_place"]:
            return "place"
        if e["_proper_people"]:
            return "person"
        if e["ph"]:
            return "phrase"
        if e["pos"] not in PLAYABLE_POS:
            return "function"
        return "common"

    for e in entries:
        e["_pool"] = pool_key(e)
        e["_unsuitable"] = 1 if e["w"].lower() in UNSUITABLE else 0
        fla = e.get("fla") or e["fl"]
        core = CORE_MAP.get(e["w"].lower())

        dmin, dmax = 1, 3
        frank, inl, ndefs = e["_frank"], e["_inl"], len(e["d"])
        # Difficulty follows the PRIMARY sense. A word like 'майдан' has a
        # dialectal secondary sense - that must not drag it into tier 3.
        flp = e["fl"]

        # --- forced HARD -------------------------------------------------
        # (curated idioms are exempt from the word-count rule: a 5-word
        #  idiom that a human vetted is legitimate HARD/MEDIUM material,
        #  while a 9-word Wiktionary proverb is not playable at all)
        too_long = e["nw"] > 6 or len(e["w"]) > 48
        if e["_sensitive"] or e["age"] == 18 or e["_unsuitable"] or too_long:
            dmin = 3
            e["_unsuitable"] = 1 if too_long else e["_unsuitable"]
        elif e["nw"] >= 4 and not core:
            dmin = 3
        if e["nw"] >= 2:
            dmin = max(dmin, 2)          # multi-word entries are never EASY
        if any(f in flp for f in HARD_FLAGS_3):
            dmin = 3
        elif any(f in flp for f in HARD_FLAGS_2):
            dmin = max(dmin, 2)
        if e["pos"] not in PLAYABLE_POS:
            dmin = 3
        if e["_pool"] in ("place", "person"):
            dmin = max(dmin, 2)
        if e["nw"] == 3:
            dmin = max(dmin, 2)
        # thin stub with no definition, no measured frequency, not curated
        if not ndefs and not frank and not core:
            dmin = max(dmin, 3)
        if len(e["w"]) < 3 and not core:
            dmin = 3

        # --- forced EASY: needs POSITIVE evidence of being a common word --
        # (article richness alone must never promote a word to easy: that is
        #  how 'офтальмолог', 'геодезія' and 'акмеїзм' used to leak into tier 1)
        earned_easy = False
        concrete = bool(CONCRETE_TOPICS.intersection(e["_topics"]))
        simple_form = (e["nw"] == 1 and e["pos"] in ("noun", "verb", "adjective")
                       and len(e["w"]) >= 3 and not e["proper"])
        if dmin == 1 and e["age"] == 6:
            if core and core["diff"] == 1:
                earned_easy = True                      # curated = trusted
            elif frank and frank <= 3000 and concrete and simple_form:
                earned_easy = True
            elif frank and frank <= 6000 and concrete and simple_form \
                    and (inl >= 8 or ndefs >= 3):
                earned_easy = True
            elif frank and frank <= 9000 and concrete and simple_form \
                    and inl >= 15 and ndefs >= 3:
                earned_easy = True
        if earned_easy:
            dmax = 1
        elif dmin == 1:
            dmin = 2                 # no evidence of commonness -> never easy

        # --- forced MEDIUM ------------------------------------------------
        if dmin <= 2 and dmax > 2:
            if ((core and core["diff"] == 2) or (frank and frank <= 12000)
                    or inl >= 5 or ndefs >= 3 or (core and core["diff"] == 1)):
                dmax = 2

        e["_dmin"], e["_dmax"] = dmin, max(dmin, dmax)

    # Fill tiers: respect [dmin, dmax], then use usage rank to hit targets.
    TARGET = {"common": (0.34, 0.34, 0.32), "phrase": (0.10, 0.30, 0.60),
              "place": (0.0, 0.45, 0.55), "person": (0.0, 0.45, 0.55),
              "function": (0.0, 0.20, 0.80)}
    for key in {e["_pool"] for e in entries}:
        items = [e for e in entries if e["_pool"] == key]
        locked = {e["w"]: None for e in items if e["_dmin"] == e["_dmax"]}
        free = [e for e in items if e["_dmin"] != e["_dmax"]]
        t = TARGET.get(key, (0.33, 0.34, 0.33))
        want = [int(len(items) * t[0]), int(len(items) * t[1]), int(len(items) * t[2])]
        have = [0, 0, 0]
        for e in items:
            if e["_dmin"] == e["_dmax"]:
                have[e["_dmin"] - 1] += 1
        free.sort(key=lambda x: -x["_usage"])     # most common first
        for e in free:
            d = None
            for cand in (1, 2, 3):
                if cand < e["_dmin"] or cand > e["_dmax"]:
                    continue
                if have[cand - 1] < want[cand - 1]:
                    d = cand
                    break
            if d is None:                          # tiers full -> take allowed min
                d = e["_dmin"] if have[e["_dmin"] - 1] <= want[e["_dmin"] - 1] else e["_dmax"]
            e["difficulty"] = d
            have[d - 1] += 1
        for e in items:
            if e["_dmin"] == e["_dmax"]:
                e["difficulty"] = e["_dmin"]
            e["usage"] = round(e.pop("_usage"), 3)
        e = None

    # ---- pass 4: actability / kid-friendliness ---------------------------
    for e in entries:
        topics = e["_topics"]
        e["actable"] = 1 if (
            e["pos"] in ("noun", "verb", "phrase") and
            e["age"] <= 12 and
            e["difficulty"] <= 2 and
            not e["proper"] and
            not e["_sensitive"] and
            not e["_unsuitable"] and
            (e["anim"] == 1 or e["pos"] == "verb" or e["_core"]
             or any(t in ACTABLE_TOPICS for t in topics)) and
            not any(t in ABSTRACT_TOPICS for t in topics)
        ) else 0
        e["kids_ok"] = 1 if (e["age"] == 6 and e["difficulty"] == 1 and
                             not e["proper"] and not e["_sensitive"] and
                             not e["_unsuitable"] and not e["ph"]) else 0
        rel_total = len(e["syn"]) + len(e["hyp"]) + len(e["hypo"]) + len(e["mer"])
        e["taboo_ok"] = 1 if (rel_total >= 2 and e["age"] != 18 and not e["proper"]) else 0

    # ---- pass 5: final row shaping ---------------------------------------
    rows = []
    for e in entries:
        rows.append({
            "w": e["w"],
            "pos": e["pos"],
            "phrase": e["ph"],
            "words": e["nw"],
            "proper": e["proper"],
            "person": e["_proper_people"],
            "place": e["_proper_place"],
            "gender": e["gen"],
            "animate": e["anim"],
            "topics": e["_topics"][:3],          # primary topic first, capped
            "difficulty": e["difficulty"],
            "age": e["age"],
            "usage": e["usage"],
            "actable": e["actable"],
            "kids": e["kids_ok"],
            "taboo": e["taboo_ok"],
            "idiom": e["_idiom"],
            "ono": e["_onomatopoeia"],
            "sens": e["_sensitive"],
            "core": e["_core"],
            "unsuit": e["_unsuitable"],
            "flags": e["fl"],
            "flags_all": e.get("fla") or e["fl"],
            "def": e["d"],
            "syn": e["syn"],
            "ant": e["ant"],
            "hyp": e["hyp"],
            "hypo": e["hypo"],
            "hol": e["hol"],
            "mer": e["mer"],
            "phr": e["phr"],
            "en": e["en"],
            "cat": e["cat"],
        })

    # ---- write JSON -------------------------------------------------------
    with open(os.path.join(OUT, "gurtom_words.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": {
            "app_uk": APP_NAME_UK, "app_en": APP_NAME_EN, "brand": BRAND,
            "source": "uk.wiktionary.org (CC BY-SA 3.0) + FrequencyWords (OpenSubtitles)",
            "entries": len(rows),
        }, "words": rows}, f, ensure_ascii=False, separators=(",", ":"))

    # ---- write SQLite (this is what ships in the APK's assets/) ----------
    db = os.path.join(OUT, "gurtom.db")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.executescript("""
    PRAGMA page_size=2048;
    PRAGMA journal_mode=OFF;
    CREATE TABLE words(
      id INTEGER PRIMARY KEY,
      w TEXT NOT NULL,
      pos TEXT NOT NULL,
      phrase INTEGER NOT NULL DEFAULT 0,
      words INTEGER NOT NULL DEFAULT 1,
      proper INTEGER NOT NULL DEFAULT 0,
      person INTEGER NOT NULL DEFAULT 0,
      place INTEGER NOT NULL DEFAULT 0,
      gender TEXT NOT NULL DEFAULT '',
      animate INTEGER NOT NULL DEFAULT -1,
      difficulty INTEGER NOT NULL DEFAULT 2,
      age INTEGER NOT NULL DEFAULT 6,
      usage REAL NOT NULL DEFAULT 0,
      actable INTEGER NOT NULL DEFAULT 0,
      kids INTEGER NOT NULL DEFAULT 0,
      taboo INTEGER NOT NULL DEFAULT 0,
      idiom INTEGER NOT NULL DEFAULT 0,
      ono INTEGER NOT NULL DEFAULT 0,
      sens INTEGER NOT NULL DEFAULT 0,
      core INTEGER NOT NULL DEFAULT 0,
      unsuit INTEGER NOT NULL DEFAULT 0,
      topics TEXT NOT NULL DEFAULT '',
      flags TEXT NOT NULL DEFAULT '',
      def TEXT NOT NULL DEFAULT '',
      syn TEXT NOT NULL DEFAULT '',
      ant TEXT NOT NULL DEFAULT '',
      hyp TEXT NOT NULL DEFAULT '',
      hypo TEXT NOT NULL DEFAULT '',
      mer TEXT NOT NULL DEFAULT '',
      phr TEXT NOT NULL DEFAULT '',
      en TEXT NOT NULL DEFAULT ''
    );
    CREATE INDEX idx_words_w ON words(w);
    CREATE INDEX idx_alias ON words(difficulty, age, unsuit, phrase, proper);
    CREATE INDEX idx_crocodile ON words(actable, age, difficulty);
    CREATE TABLE party(
      id INTEGER PRIMARY KEY,
      kind TEXT NOT NULL,
      age INTEGER NOT NULL DEFAULT 6,
      text TEXT NOT NULL
    );
    CREATE INDEX idx_party ON party(kind, age);
    CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
    """)
    J = lambda v: json.dumps(v, ensure_ascii=False)
    # keep the DB lean: 3 definitions, truncated; no raw category dump
    D = lambda r: J([x[:200] for x in r["def"][:3]])
    cols = ("w,pos,phrase,words,proper,person,place,gender,animate,difficulty,age,"
            "usage,actable,kids,taboo,idiom,ono,sens,core,unsuit,topics,flags,"
            "def,syn,ant,hyp,hypo,mer,phr,en")
    con.executemany(
        f"INSERT INTO words({cols}) VALUES(" + "?," * 29 + "?)",
        [(r["w"], r["pos"], r["phrase"], r["words"], r["proper"], r["person"],
          r["place"], r["gender"], r["animate"], r["difficulty"], r["age"],
          r["usage"], r["actable"], r["kids"], r["taboo"], r["idiom"], r["ono"],
          r["sens"], r["core"], r["unsuit"], J(r["topics"]), J(r["flags"]),
          D(r), J(r["syn"][:8]), J(r["ant"][:6]), J(r["hyp"][:6]),
          J(r["hypo"][:6]), J(r["mer"][:6]), J(r["phr"][:6]), J(r["en"][:4]))
         for r in rows])
    con.executemany("INSERT INTO party(kind,age,text) VALUES(?,?,?)",
                    list(party_content.iter_cards()))
    con.execute("INSERT INTO meta VALUES('app_uk',?)", (APP_NAME_UK,))
    con.execute("INSERT INTO meta VALUES('app_en',?)", (APP_NAME_EN,))
    con.execute("INSERT INTO meta VALUES('brand',?)", (BRAND,))
    con.execute("INSERT INTO meta VALUES('source',?)",
                ("uk.wiktionary.org (CC BY-SA 3.0) + FrequencyWords (OpenSubtitles)",))
    con.execute("INSERT INTO meta VALUES('entries',?)", (str(len(rows)),))
    con.commit()
    con.execute("VACUUM")
    con.commit()
    con.close()

    # gzip variant for APK assets - SQLite compresses ~3x, so shipping
    # assets/gurtom.db.gz and inflating on first run keeps the APK smaller
    import gzip
    import shutil
    with open(db, "rb") as fi, gzip.open(db + ".gz", "wb", compresslevel=9) as fo:
        shutil.copyfileobj(fi, fo)

    # ---- topics.json -------------------------------------------------------
    with open(os.path.join(OUT, "topics.json"), "w", encoding="utf-8") as f:
        json.dump([{"id": t, "uk": uk, "en": en} for t, uk, en, _ in TOPICS],
                  f, ensure_ascii=False, indent=1)

    # ---- party cards JSON --------------------------------------------------
    party_rows = list(party_content.iter_cards())
    with open(os.path.join(OUT, "party_content.json"), "w", encoding="utf-8") as f:
        json.dump([{"kind": k, "age": a, "text": t} for k, a, t in party_rows],
                  f, ensure_ascii=False, indent=0)

    # ---- QA report ---------------------------------------------------------
    def cnt(pred):
        return sum(1 for r in rows if pred(r))

    playable = [r for r in rows
                if r["pos"] in PLAYABLE_POS and r["age"] != 18 and not r["sens"]]
    play_ids = {id(r) for r in playable}
    tc = Counter()
    for r in playable:
        for t in r["topics"]:
            tc[t] += 1

    summary = {
        "total_entries": len(rows),
        "db_size_bytes": os.path.getsize(db),
        "json_size_bytes": os.path.getsize(os.path.join(OUT, "gurtom_words.json")),
        "by_pos": dict(Counter(r["pos"] for r in rows).most_common()),
        "by_difficulty": dict(sorted(Counter(r["difficulty"] for r in rows).items())),
        "by_age": dict(sorted(Counter(r["age"] for r in rows).items())),
        "playable_pool": len(playable),
        "playable_difficulty": dict(sorted(Counter(r["difficulty"] for r in playable).items())),
        "single_word_playable": cnt(lambda r: id(r) in play_ids and not r["phrase"] and not r["proper"]),
        "phrases_total": cnt(lambda r: r["phrase"] or r["idiom"]),
        "phrases_2w": cnt(lambda r: r["words"] == 2 and not r["proper"]),
        "phrases_3w_plus": cnt(lambda r: r["words"] >= 3 and not r["proper"]),
        "proper_people": cnt(lambda r: r["person"]),
        "proper_places": cnt(lambda r: r["place"]),
        "actable": cnt(lambda r: r["actable"]),
        "kids_6plus_easy": cnt(lambda r: r["kids"]),
        "taboo_ready": cnt(lambda r: r["taboo"]),
        "with_english": cnt(lambda r: r["en"]),
        "with_synonyms": cnt(lambda r: r["syn"]),
        "with_definitions": cnt(lambda r: r["def"]),
        "blocked_18plus": cnt(lambda r: r["age"] == 18),
        "sensitive": cnt(lambda r: r["sens"]),
        "topic_counts": dict(tc.most_common()),
        "party_cards": len(party_rows),
        "party_by_kind": dict(Counter(k for k, _a, _t in party_rows).most_common()),
    }
    with open(os.path.join(OUT, "pools_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    lines = ["# Gurtom / Together - word bank QA report", ""]
    lines.append(f"- Total entries: **{summary['total_entries']}**")
    lines.append(f"- SQLite size: **{summary['db_size_bytes']/1e6:.2f} MB**")
    lines.append(f"- JSON size: **{summary['json_size_bytes']/1e6:.2f} MB**")
    lines.append(f"- Playable pool (no 18+/sensitive): **{summary['playable_pool']}**")
    lines.append("")
    lines.append("## Difficulty distribution (playable)")
    for k, v in summary["playable_difficulty"].items():
        lines.append(f"- Level {k}: {v} ({v/max(1,summary['playable_pool'])*100:.1f}%)")
    lines.append("")
    lines.append("## Age gates")
    for k, v in summary["by_age"].items():
        lines.append(f"- {k}+: {v}")
    lines.append("")
    lines.append("## Game pools")
    for k in ("single_word_playable", "phrases_total", "phrases_2w", "phrases_3w_plus",
              "proper_people", "proper_places", "actable", "kids_6plus_easy",
              "taboo_ready", "with_english", "with_synonyms", "with_definitions"):
        lines.append(f"- {k}: {summary[k]}")
    lines.append("")
    lines.append("## Topics")
    for t, c in tc.most_common():
        label = next((x[1] for x in TOPICS if x[0] == t), t)
        lines.append(f"- {label} ({t}): {c}")
    lines.append("")
    lines.append("## POS")
    for p, c in summary["by_pos"].items():
        lines.append(f"- {POS_LABEL.get(p,p)} ({p}): {c}")
    with open(os.path.join(OUT, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(json.dumps(summary, ensure_ascii=False, indent=1)[:3000], file=sys.stderr)


if __name__ == "__main__":
    main()
