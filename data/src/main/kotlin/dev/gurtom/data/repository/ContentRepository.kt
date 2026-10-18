// ContentRepository.kt — доступ до слів і карток через DAO з виключенням повторів (DATA_SCHEMA §6).
package dev.gurtom.data.repository

import dev.gurtom.core.common.DefaultDispatcher
import dev.gurtom.core.common.Result
import dev.gurtom.core.common.runCatchingResult
import dev.gurtom.core.database.dao.PartyDao
import dev.gurtom.core.database.dao.WordsDao
import dev.gurtom.data.model.GameType
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext

/**
 * Репозиторій контенту: єдина точка, де шар :data читає словник.
 * Guarantees: `sens=1` та `unsuit=1` ніколи не повертаються (фільтри в DAO),
 * повторів у межах сесії позбуваються через [usedIds].
 */
@Singleton
class ContentRepository @Inject constructor(
    private val wordsDao: WordsDao,
    private val partyDao: PartyDao,
    @DefaultDispatcher private val default: CoroutineDispatcher,
) {

    /** Витягує [limit] свіжих карток для гри [game] з урахуванням віку гравців. */
    suspend fun drawWords(
        game: GameType,
        maxAge: Int,
        usedIds: Set<Long>,
        limit: Int,
    ): Result<List<WordCard>> = withContext(default) {
        runCatchingResult {
            val exclude = usedIds.toList()
            when (game) {
                GameType.Crocodile -> wordsDao.crocodilePool(maxAge, exclude, limit)
                GameType.WhoAmI -> wordsDao.whoAmIPool(maxAge, exclude, limit)
                GameType.Taboo -> wordsDao.tabooPool(maxAge, exclude, limit)
                else -> wordsDao.aliasPool(maxAge, exclude, limit)
            }.map {
                WordCard(
                    id = it.id,
                    word = it.w,
                    definitionHint = it.def.orEmpty(),
                    synonymsRaw = it.syn.orEmpty(),
                )
            }
        }
    }

    /** Картки вечірніх ігор (Правда/Дія, Ніколи не, …) за kind із таблиці party. */
    suspend fun drawPartyCards(
        kind: String,
        maxAge: Int,
        usedIds: Set<Long>,
        limit: Int,
    ): Result<List<PartyCard>> = withContext(default) {
        runCatchingResult {
            partyDao.draw(kind, maxAge, usedIds.toList(), limit).map {
                PartyCard(id = it.id, kind = it.kind, text = it.text)
            }
        }
    }
}

/** Спрощена модель слова для UI-шару (без JSON-полів БД). */
data class WordCard(
    val id: Long,
    val word: String,
    val definitionHint: String,
    val synonymsRaw: String,
)

/** Спрощена модель картки party; для emoji текст ділити по першому '|'. */
data class PartyCard(
    val id: Long,
    val kind: String,
    val text: String,
)
