# DATA_SCHEMA.md — контракт даних для застосунку Ґуртом / Together

Цей файл — **єдине джерело правди** про формат контенту. Будь-який код, який
читає словник, має орієнтуватися на нього. Файл лежить у репозиторії, щоб
кожен наступний промпт для кодера міг на нього послатися.

---

## 1. Розташування і розпакування

| | |
|---|---|
| У репозиторії | `app/src/main/assets/gurtom.db.gz` (2.9 МБ) |
| У пристрої | `context.filesDir/gurtom.db` (11.9 МБ, read-only) |
| Формат | SQLite 3, UTF-8, таблиці `words`, `party`, `meta` |

**Розпакування (обов'язково в фоні, не на Main):**

```kotlin
class WordDatabaseAssetUnpacker(private val context: Context) {
    private val target get() = File(context.filesDir, "gurtom.db")

    /** Ідемпотентне: якщо файл уже розпаковано і версія збігається — нічого не робить. */
    suspend fun ensureUnpacked(): File = withContext(Dispatchers.IO) {
        val versionInAssets = context.assets.open("gurtom.db.gz").use { gz ->
            // версія лежить у meta; читаємо її після розпакування, тому
            // спершу перевіряємо маркер-файл
            readInstalledVersion()
        }
        if (target.exists() && versionInAssets == BUILD_DATA_VERSION) return@withContext target

        val tmp = File(context.filesDir, "gurtom.db.tmp")
        context.assets.open("gurtom.db.gz").use { input ->
            GZIPInputStream(input).use { gzip ->
                tmp.outputStream().use { gzip.copyTo(it, DEFAULT_BUFFER_SIZE * 8) }
            }
        }
        if (!tmp.renameTo(target)) error("Не вдалося активувати базу даних")
        writeInstalledVersion(BUILD_DATA_VERSION)
        target
    }
    // readInstalledVersion / writeInstalledVersion — файл .gurtom-data-version у filesDir
    companion object { const val BUILD_DATA_VERSION = 1 }
}
```

**Сплеш-анімація має прикривати цей крок.** Розпакування займає ~150–300 мс
на середньому пристрої, але на бюджетному може бути 1–2 с — тому показуємо
сплеш, поки `ensureUnpacked()` не завершиться, і лише потім пускаємо в Home.
Якщо розпакування впало — показуємо екран помилки з кнопкою «Спробувати ще»
(не краш).

**Відкриття:** `SQLiteDatabase.openDatabase(file, null, OPEN_READONLY)`.
Можна використовувати Room з `Room.databaseBuilder(...).createFromAsset()` —
але `createFromAsset` **не вміє** у gzip, тому розпаковуємо самі й віддаємо
Room уже розпакований шлях через `.setJournalMode(SimpleAutoClosingDatabase)`.
Простіше і швидше: прямий `SupportSQLite`/`SQLiteDatabase` + власний DAO-шар.

---

## 2. Таблиця `words`

| Колонка | Тип | Опис |
|---|---|---|
| `id` | INTEGER PK | Стабільний ідентифікатор. **Використовуй його, а не текст**, щоб виключати повторення в межах гри |
| `w` | TEXT | Саме слово або фраза, українською, у нижньому регістрі (власні назви — з великої) |
| `pos` | TEXT | `noun` `verb` `adjective` `adverb` `phrase` `participle` `gerund` `pronoun` `numeral` `preposition` `conjunction` `particle` `interjection` `predicative` `other` |
| `phrase` | INTEGER 0/1 | 1 = багатослівний запис або фразеологізм |
| `words` | INTEGER | Кількість слів у записі (1 для одиночних) |
| `proper` | INTEGER 0/1 | Власна назва |
| `person` | INTEGER 0/1 | Власна назва — **людина** (прізвище, ім'я, псевдонім). Пул для «Хто я?» |
| `place` | INTEGER 0/1 | Власна назва — **місце** (топонім, село, місто, область, річка) |
| `gender` | TEXT | `m` / `f` / `n` / `''` (невідомо). **Критично для «Хто я?»**: підказка «Я — лікар» vs «Я — лікарка» |
| `animate` | INTEGER | `1` = істота, `0` = неістота, `-1` = невідомо |
| `difficulty` | INTEGER | `1` легко · `2` середньо · `3` складно |
| `age` | INTEGER | `6` · `12` · `18`. Візьми запис, якщо `age <= maxAge` користувача |
| `usage` | REAL | Сиримірна «вживаність» (частотність + in-links + полісемія). Для сортування «найвідоміші першими» |
| `actable` | INTEGER 0/1 | 1 = слово можна **показати** без слів. Пул для Крокодила |
| `kids` | INTEGER 0/1 | 1 = підходить для дитячого режиму 6+ |
| `taboo` | INTEGER 0/1 | 1 = є ≥2 семантичні зв'язки, тож можна зібрати 5 заборонених слів |
| `idiom` | INTEGER 0/1 | Фразеологізм / стала фраза |
| `ono` | INTEGER 0/1 | Звуконаслідувальне (для режиму «Звуки») |
| `sens` | INTEGER 0/1 | **Чутливий контент. Завжди виключай з вибірки**, окрім явного opt-in |
| `core` | INTEGER 0/1 | 1 = слово з курируваного базового списку (найнадійніша якість) |
| `unsuit` | INTEGER 0/1 | 1 = граматична службова одиниця або надто довга фраза. **Завжди виключай** (`unsuit=0`) |
| `topics` | TEXT (JSON array) | До 3 ідентифікаторів тем, перша = основна. Див. §4 |
| `flags` | TEXT (JSON array) | Стилістичні маркери **первинного** значення: `archaic` `colloquial` `slang` `dialect` `figurative` `humorous` `solemn` `pejorative` `technical` `political` `religious` `anatomy` `biology` `military` `legal` `medical` `rare` `chemistry` `sports` `music` `culinary` `it` `vulgar` |
| `def` | TEXT (JSON array) | До 3 означень, кожне ≤200 символів. Використовуй як підказку |
| `syn` | TEXT (JSON array) | Синоніми (до 8) |
| `ant` | TEXT (JSON array) | Антоніми (до 6) |
| `hyp` | TEXT (JSON array) | Гіпероніми — «це різновид ЧОГО» (до 6) |
| `hypo` | TEXT (JSON array) | Гіпоніми — «різновиди ЦЬОГО» (до 6) |
| `mer` | TEXT (JSON array) | Мероніми — частини цілого (до 6) |
| `phr` | TEXT (JSON array) | Фразеологізми з цим словом (до 6) |
| `en` | TEXT (JSON array) | Англійські відповідники (до 4). 13 982 записи мають переклад |
| ~~`cat`~~ | — | **Немає в БД** (сирі категорії Вікісловника лишилися лише в JSON для дебагу) |

### 2.1 JSON-поля

Усі масиви серіалізовані як компактний JSON-рядок: `["медик","доктор"]`.
Порожній масив = `'[]'` (**не** NULL і не `''`). Парсимо через
`org.json.JSONArray` (входить у Android) або kotlinx.serialization:

```kotlin
private val json = Json { ignoreUnknownKeys = true }
fun SupportSQLiteCursor.stringList(col: Int): List<String> =
    getString(col)?.takeIf { it.length > 2 }
        ?.let { json.decodeFromString<List<String>>(it) }
        ?: emptyList()
```

**Уникай `JSON.parse` для кожного рядка в циклі вибірки 500 слів** — парси лише
ті записи, які реально показуєш (сторінками по 50–100), або зберігай уже
розпарсені об'єкти в пам'яті на час гри.

---

## 3. Таблиця `party` (картки без слів)

| Колонка | Тип | Опис |
|---|---|---|
| `id` | INTEGER PK | |
| `kind` | TEXT | `truth` · `dare` · `never` · `likely` · `emoji` · `forfeit` |
| `age` | INTEGER | `6` · `12` · `18` |
| `text` | TEXT | Текст картки |

**Особливість `emoji`:** текст має формат `емодзі|відповідь`, наприклад
`🦁👑|Король Лев`. Розділюй по **першому** символі `|`:

```kotlin
val (puzzle, answer) = text.substringBefore('|') to text.substringAfter('|')
```

Кількість карток станом на збірку датасету v1:

```
truth 100 (50×6+ · 40×12+ · 10×18+)     never   80 (30/30/20)
dare   90 (50×6+ · 30×12+ · 10×18+)     likely  69 (30/20/19)
emoji  60 (40×6+ · 20×12+)              forfeit 50 (20/20/10)
                                       ─────────────────────
                                        Разом  449
```

Це **стартова колода**. Її достатньо, щоб гра не повторювалася протягом
10–15 сесій, але для утримання користувача плануй розширення до 300+ на вид
у v1.1 (редагуй `tools/party_content.py` і перебілдуй — перебілд БД займає 20 с).

---

## 4. Теми (`topics.json` → 26 штук)

| id | Українською | English | Записів |
|---|---|---|---|
| `buildings` | Будівлі та місця | Buildings & Places | 3808 |
| `actions` | Дії та рух | Actions & Motion | 2485 |
| `language` | Мова та слова | Language & Words | 2072 |
| `people` | Людина та родина | People & Family | 1613 |
| `geography` | Географія та подорожі | Geography & Travel | 1438 |
| `science_tech` | Наука й техніка | Science & Tech | 1262 |
| `profession` | Професії та робота | Jobs & Work | 1254 |
| `time_abstract` | Час і абстрактні поняття | Time & Abstract | 1143 |
| `society` | Суспільство та економіка | Society & Money | 975 |
| `home` | Дім і побут | Home & Objects | 935 |
| `art_music` | Мистецтво та музика | Art & Music | 839 |
| `body` | Тіло та здоров'я | Body & Health | 815 |
| `emotions` | Емоції та характер | Emotions & Character | 787 |
| `traits` | Ознаки та якості | Traits & Qualities | 775 |
| `food` | Їжа та напої | Food & Drinks | 710 |
| `plants` | Рослини й природа | Plants & Nature | 623 |
| `animals` | Тварини | Animals | 586 |
| `religion_myth` | Релігія та міфи | Religion & Myth | 399 |
| `transport` | Транспорт | Transport | 395 |
| `nature_weather` | Природа та погода | Nature & Weather | 391 |
| `clothes` | Одяг і взуття | Clothes & Shoes | 377 |
| `sport` | Спорт та ігри | Sport & Games | 304 |
| `war` | Війна та зброя | War & Weapons | 302 |
| `farm` | Село та господарство | Farm & Countryside | 279 |
| `culture` | Культура та традиції | Culture & Traditions | 279 |
| `school` | Школа та освіта | School & Education | 265 |

`topics` — це JSON-масив, тож **звичайний `WHERE topics=?` не працює**.
Фільтруємо так:

```sql
-- варіант 1: LIKE (просто, досить швидко при 43k рядків і наявному індексі на difficulty)
SELECT * FROM words
WHERE difficulty = ? AND age <= ? AND unsuit = 0 AND sens = 0
  AND topics LIKE '%"animals"%'
ORDER BY RANDOM() LIMIT 30;

-- варіант 2 (краще): витягни id потрібних записів одним запитом без фільтра
-- по темах і відфільтруй теми в Kotlin — тем лише 26, це дешево
```

**Увага:** ~10k записів мають порожній `topics` (`'[]'`). Це нормально —
коли користувач обирає «Усі теми», фільтр не застосовується взагалі.

---

## 5. Як будувати запит для кожної гри

Усі запити **обов'язково** містять базовий запобіжник:

```sql
AND unsuit = 0 AND sens = 0 AND age <= :maxAge
```

### Аліас
```sql
SELECT id, w, def, syn, phrase FROM words
WHERE unsuit=0 AND sens=0 AND age <= :maxAge
  AND proper = 0                       -- власні назви ламають «поясни словами»
  AND pos IN ('noun','verb','adjective','adverb','phrase')
  AND difficulty = :difficulty
  AND (:topicsEmpty OR topics LIKE :topicPattern)
ORDER BY RANDOM() LIMIT :batch
```
На складному рівні (`difficulty=3`) **дозволь `proper=1` і фрази** — саме там
цікаві фразеологізми. На легкому — тільки `phrase=0 AND words=1`.

**Фолбек:** якщо вибірка <20, послаблюй у такому порядку і логуй подію:
`age → 12`, потім `difficulty ± 1`, потім знімай фільтр тем.

### Крокодил
```sql
SELECT id, w, def, topics FROM words
WHERE actable=1 AND unsuit=0 AND sens=0 AND age <= :maxAge
  AND difficulty <= :difficulty        -- <= а не =, бо пул менший
ORDER BY RANDOM() LIMIT :batch
```
Пулу 4 637 (1 970 легких + 2 667 середніх) вистачає на десятки ігор.

### Хто я?
```sql
SELECT id, w, gender, def, animate FROM words
WHERE unsuit=0 AND sens=0 AND age <= :maxAge
  AND (animate = 1 OR person = 1 OR actable = 1)
  AND difficulty <= :difficulty
ORDER BY RANDOM() LIMIT :batch
```
`gender` використовуємо для підказки на екрані: при `gender='f'` показуємо
«Вона», при `m` — «Він», при `n` — «Воно», при `''` — без підказки.

### Табу
```sql
SELECT id, w, syn, hyp, hypo, mer, def FROM words
WHERE taboo=1 AND unsuit=0 AND sens=0 AND age <= :maxAge
  AND difficulty <= :difficulty
ORDER BY RANDOM() LIMIT :batch
```
**Формування 5 заборонених слів (робиться в Kotlin):**
1. Обов'язково — саме слово `w`.
2. Обов'язково — корінь слова (перші 4+ символи) як підрядок: забороняємо
   також похідні, порівнюй `caseInsensitive` і `contains`.
3. Далі за пріоритетом: `hyp` → `syn` → `hypo` → `mer`, поки не набереться 5.
4. Якщо зв'язків менше 5 — добирай випадковими словами з тієї ж теми
   (`topics[0]`), але позначай таку карту прапорцем `weak=true` і не показуй
   її на легкому рівні.

### Капелюх
Той самий пул, що й Аліас, **але** набір слів фіксується на всю гру
(зазвичай 60–120 слів) і пере використовується в трьох раундах. Раунд 3
(«одним словом») вимагає коротких слів: додатково `AND words = 1 AND length(w) <= 12`.

### Слова-ланцюжок
```sql
SELECT id, w FROM words
WHERE unsuit=0 AND sens=0 AND age <= :maxAge
  AND words = 1 AND phrase = 0 AND proper = 0
  AND pos IN ('noun','adjective')
  AND w LIKE :lastLetter || '%'        -- починається на потрібну літеру
  AND length(w) BETWEEN 3 AND 20
```
**Правило літери:** з кінця слова відкидаємо `ь`, `й`, `'`, `’` — і беремо
останню значущу літеру. Для наступного ходу шукаємо слова, що починаються
на неї. Якщо `w LIKE ?%` повертає <3 варіанти — дозволь ігнорувати м'який знак
на початку й розшир до `pos IN ('noun','adjective','verb')`.

**Валідація вводу гравця** — лише запитом до БД (`EXISTS`), жодних локальних
словників. Це і є «чесний арбітр».

### Правда чи дія / Ніколи не / Хто найбільше / Емодзі / Фанти
```sql
SELECT id, text FROM party
WHERE kind = :kind AND age <= :maxAge
ORDER BY RANDOM() LIMIT :batch
```
Для «Правда чи дія» тягни **по одній** картці `truth` і `dare` одночасно
і показуй вибір. Не допускай повторів у межах сесії (тримай `Set<Long>`
показаних `id` у `ViewModel`).

---

## 6. Виключення повторів у межах гри

Обов'язкова вимога UX: **слово не повинно повторюватися в межах однієї гри.**

```kotlin
class WordSelector(private val repo: WordRepository) {
    private val used = mutableSetOf<Long>()
    private var buffer: ArrayDeque<WordEntry> = ArrayDeque()

    suspend fun next(filter: WordFilter, batchSize: Int = 50): WordEntry? {
        while (buffer.isEmpty()) {
            val page = repo.query(filter.copy(excludeIds = used.toList(), limit = batchSize))
            if (page.isEmpty()) {
                if (used.size >= filter.softCap) used.clear()   // пул вичерпано — починаємо заново
                else return null
            }
            buffer.addAll(page)
        }
        val w = buffer.removeFirst()
        used += w.id
        return w
    }
    fun reset() { used.clear(); buffer.clear() }
}
```

`WHERE id NOT IN (...)` з 500+ ідентифікаторами стає повільним. Після ~300
використаних слів переходь на `used`-фільтрацію **в пам'яті**: тягни сторінку
в 100 записів без `NOT IN` і відкидай вже використані в Kotlin.

---

## 7. Продуктивність

| Операція | Ціль |
|---|---|
| Розпакування `gurtom.db.gz` (перший запуск) | <300 мс середній пристрій, <2 с бюджетний |
| Відкриття БД | <50 мс |
| Вибірка 50 слів із фільтром | <25 мс |
| Валідація одного слова в «ланцюжку» | <5 мс (`EXISTS` за індексом `idx_words_w`) |
| Холодний старт до Home | <1.5 с (без розпакування), <2.5 с (перший запуск) |
| Пам'ять | Не тримай у пам'яті всі 43k записів. Максимум — 200–500 на гру |

**Індекси, які вже є в БД:** `idx_words_w(w)`,
`idx_alias(difficulty, age, unsuit, phrase, proper)`, `idx_crocodile(actable, age, difficulty)`,
`idx_party(kind, age)`. Не додавай нових індексів без вимірювання —
вони збільшують файл.

---

## 8. Локалізація даних

**Українська** — повна (43 141 запис). **Англійська** у v1.0 — тільки UI-рядки;
ігровий контент лишається українським.

Для EN-версії ігрового контенту в v1.1 є два шляхи:
1. **Готовий частковий:** 13 982 записи мають `en` (англійські відповідники з
   Вікісловника). Це дає EN-пул ~14k слів, але **без** EN-означень і EN-синонімів,
   тож Табу й підказки працюватимуть гірше.
2. **Рекомендований:** окрема курація EN core-списку (2–3k слів) за тією ж
   методикою, що й `tools/core_vocab.py`. Для вечіркових ігор 2 000 слів — це
   вже 30+ годин геймплею.

**Важливо для UI:** коли мова інтерфейсу EN, а контент UK, показуй явну плашку
«Слова українською» на екрані налаштувань, щоб не було враження багу.

---

## 9. Версіонування даних

`meta` таблиця:

| k | v |
|---|---|
| `app_uk` | `Ґуртом` |
| `app_en` | `Together` |
| `brand` | `mufidev` |
| `source` | `uk.wiktionary.org (CC BY-SA 3.0) + FrequencyWords (OpenSubtitles)` |
| `entries` | `43141` |

При оновленні датасету збільшуй `BUILD_DATA_VERSION` у коді розпакувальника
і записуй цю версію в `meta`. Це дає безпечну міграцію: старий файл
перезаписується новим при першому запуску оновленої версії застосунку.

---

## 10. Атрибуція (обов'язково в застосунку)

Екран «Налаштування → Ліцензії та джерела даних» має містити дослівно:

> **Джерела даних**
> Словник створено на основі матеріалів Вікісловника (uk.wiktionary.org),
> доступних на умовах ліцензії Creative Commons Attribution-ShareAlike 3.0
> Unported (CC BY-SA 3.0). Частотні дані — FrequencyWords (OpenSubtitles).
> Додаткова курація, класифікація за темами та оцінка складності — mufidev.
>
> Повний текст ліцензії: https://creativecommons.org/licenses/by-sa/3.0/

Плюс файл `app/src/main/assets/ATTRIBUTION.txt` з тим самим текстом,
плюс абзац в описі Play Store. Це не формальність: CC BY-SA вимагає
видимого зазначення авторства, і його відсутність — підстава для скарги.
