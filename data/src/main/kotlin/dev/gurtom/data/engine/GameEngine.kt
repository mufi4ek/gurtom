// GameEngine.kt — скелет ігрового рушія: стан раунду й видача карток без повторів.
package dev.gurtom.data.engine

import dev.gurtom.core.common.Result
import dev.gurtom.data.model.GameType
import dev.gurtom.data.repository.ContentRepository
import dev.gurtom.data.repository.WordCard
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Рушій гри: тримає набір використаних id у межах сесії (DATA_SCHEMA §6)
 * і видає наступну картку через [ContentRepository]. Справжня механіка
 * (таймери, команди, рахунок) нарощується на цей контракт.
 */
@Singleton
class GameEngine @Inject constructor(
    private val content: ContentRepository,
) {

    private val usedIds = mutableSetOf<Long>()

    /** Наступне слово для гри; порожній список => пул вичерпано. */
    suspend fun nextWord(game: GameType, maxAge: Int): Result<List<WordCard>> =
        content.drawWords(game, maxAge, usedIds.toSet(), limit = 1).also { result ->
            if (result is Result.Ok) usedIds += result.data.map { it.id }
        }

    /** Скидає лічильник повторів — викликати на старті нової партії. */
    fun reset() {
        usedIds.clear()
    }
}
