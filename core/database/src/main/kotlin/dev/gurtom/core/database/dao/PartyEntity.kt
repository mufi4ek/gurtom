// PartyEntity.kt — Row-мапінг таблиці `party` (картки без слів), DATA_SCHEMA §3.
package dev.gurtom.core.database.dao

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Картка вечірніх ігор. kind: truth/dare/never/likely/emoji/forfeit.
 * Для emoji текст має формат `емодзі|відповідь` — ділити по першому '|'.
 */
@Entity(tableName = "party")
data class PartyEntity(
    @PrimaryKey
    @ColumnInfo(name = "id") val id: Long,

    @ColumnInfo(name = "kind") val kind: String,

    /** вікове обмеження: 6 · 12 · 18. */
    @ColumnInfo(name = "age") val age: Int,

    @ColumnInfo(name = "text") val text: String,
)
