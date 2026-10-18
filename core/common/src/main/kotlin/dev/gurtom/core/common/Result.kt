// Result.kt — уніфікований обгортник успіху/помилки для всіх шарів проєкту.
package dev.gurtom.core.common

/**
 * Результат операції: [Ok] із даними або [Error] з причиною.
 * Використовується репозиторіями замість винятків на межі потоків.
 */
sealed interface Result<out T> {

    /** Успішне завершення з значенням [data]. */
    data class Ok<T>(val data: T) : Result<T>

    /** Помилка; [cause] зберігається для логування, текст показувати не можна. */
    data class Error(val cause: Throwable? = null) : Result<Nothing>

    companion object {
        fun <T> ok(data: T): Result<T> = Ok(data)
        fun error(cause: Throwable? = null): Result<Nothing> = Error(cause)
    }
}

/** Виконує [block], перетворюючи виняток у [Result.Error]. */
inline fun <T> runCatchingResult(block: () -> T): Result<T> =
    try {
        Result.ok(block())
    } catch (t: Throwable) {
        Result.error(t)
    }
