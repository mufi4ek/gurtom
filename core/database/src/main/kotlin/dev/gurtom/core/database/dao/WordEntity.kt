// WordEntity.kt — Row-мапінг таблиці `words` згідно з DATA_SCHEMA §2.
package dev.gurtom.core.database.dao

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Запис словника. Назви полів навмисно короткі — як колонки БД;
 * JSON-масиви (syn/hyp/…) лишаються сирими рядками, парсить їх шар :data.
 */
@Entity(tableName = "words")
data class WordEntity(
    @PrimaryKey
    @ColumnInfo(name = "id") val id: Long,

    /** Саме слово/фраза українською. */
    @ColumnInfo(name = "w") val w: String,

    /** частина мови: noun/verb/adjective/… */
    @ColumnInfo(name = "pos") val pos: String?,

    @ColumnInfo(name = "proper") val proper: Int = 0,
    @ColumnInfo(name = "person") val person: Int = 0,
    @ColumnInfo(name = "place") val place: Int = 0,

    /** рід: m/f/n/''. */
    @ColumnInfo(name = "gender") val gender: String? = "",

    /** 1 істота, 0 неістота, -1 невідомо. */
    @ColumnInfo(name = "animate") val animate: Int = -1,

    /** 1 легко · 2 середньо · 3 складно. */
    @ColumnInfo(name = "difficulty") val difficulty: Int = 2,

    /** вікове обмеження: 6 · 12 · 18. */
    @ColumnInfo(name = "age") val age: Int = 18,

    /** сиримірна вживаність для сортування. */
    @ColumnInfo(name = "usage") val usage: Double = 0.0,

    @ColumnInfo(name = "actable") val actable: Int = 0,
    @ColumnInfo(name = "kids") val kids: Int = 0,
    @ColumnInfo(name = "taboo") val taboo: Int = 0,

    /** чутливий контент — завжди виключати з вибірки без opt-in. */
    @ColumnInfo(name = "sens") val sens: Int = 0,

    /** граматична службова одиниця — завжди виключати. */
    @ColumnInfo(name = "unsuit") val unsuit: Int = 0,

    @ColumnInfo(name = "topics") val topics: String? = "[]",
    @ColumnInfo(name = "def") val def: String? = "[]",
    @ColumnInfo(name = "syn") val syn: String? = "[]",
    @ColumnInfo(name = "ant") val ant: String? = "[]",
    @ColumnInfo(name = "hyp") val hyp: String? = "[]",
    @ColumnInfo(name = "hypo") val hypo: String? = "[]",
    @ColumnInfo(name = "mer") val mer: String? = "[]",
)
