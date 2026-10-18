// WordsDao.kt + PartyDao.kt — запити до словника та карток (DATA_SCHEMA §5–§6).
package dev.gurtom.core.database.dao

import androidx.room.Dao
import androidx.room.Query

/**
 * DAO таблиці `words`. Усі запити гарантовано виключають `sens=1` і `unsuit=1`
 * вимогами продукту; повторів у межах гри позбуваються фільтрацією по [excludeIds].
 */
@Dao
interface WordsDao {

    /** Вибірка для Аліасу: будь-які pos, службові виключені. */
    @Query(
        """
        SELECT * FROM words
        WHERE unsuit = 0 AND sens = 0 AND age <= :maxAge
          AND id NOT IN (:excludeIds)
        ORDER BY usage DESC
        LIMIT :limit
        """,
    )
    suspend fun aliasPool(maxAge: Int, excludeIds: List<Long>, limit: Int): List<WordEntity>

    /** Вибірка для Крокодила: лише показувані слова. */
    @Query(
        """
        SELECT * FROM words
        WHERE actable = 1 AND unsuit = 0 AND sens = 0 AND age <= :maxAge
          AND id NOT IN (:excludeIds)
        ORDER BY RANDOM()
        LIMIT :limit
        """,
    )
    suspend fun crocodilePool(maxAge: Int, excludeIds: List<Long>, limit: Int): List<WordEntity>

    /** Вибірка для «Хто я?»: істоти/люди/показувані. */
    @Query(
        """
        SELECT * FROM words
        WHERE (animate = 1 OR person = 1 OR actable = 1)
          AND unsuit = 0 AND sens = 0 AND age <= :maxAge
          AND id NOT IN (:excludeIds)
        ORDER BY RANDOM()
        LIMIT :limit
        """,
    )
    suspend fun whoAmIPool(maxAge: Int, excludeIds: List<Long>, limit: Int): List<WordEntity>

    /** Вибірка для Табу: слова з ≥2 семантичними зв'язками. */
    @Query(
        """
        SELECT * FROM words
        WHERE taboo = 1 AND unsuit = 0 AND sens = 0 AND age <= :maxAge
          AND id NOT IN (:excludeIds)
        ORDER BY RANDOM()
        LIMIT :limit
        """,
    )
    suspend fun tabooPool(maxAge: Int, excludeIds: List<Long>, limit: Int): List<WordEntity>

    /** Запис за стабільним id (для перевірених повторів/підказок). */
    @Query("SELECT * FROM words WHERE id = :id LIMIT 1")
    suspend fun byId(id: Long): WordEntity?
}

/** DAO таблиці `party` — картки Правда/Дія, Ніколи не, Хто найбільше, Емодзі, Фанти. */
@Dao
interface PartyDao {

    @Query(
        """
        SELECT * FROM party
        WHERE kind = :kind AND age <= :maxAge AND id NOT IN (:excludeIds)
        ORDER BY RANDOM()
        LIMIT :limit
        """,
    )
    suspend fun draw(kind: String, maxAge: Int, excludeIds: List<Long>, limit: Int): List<PartyEntity>
}
