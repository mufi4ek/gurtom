// SplashLogic.kt — чиста (без Android/Compose) модель готовності сплешу: перехід на Home лише коли анімація І розпакування БД завершилися (PLAN §4.2).
package dev.gurtom.feature.splash

/** Події, що рухають стан сплешу. */
sealed interface SplashEvent {
    data object AnimationFinished : SplashEvent
    data object UnpackFinished : SplashEvent
    data class UnpackFailed(val message: String) : SplashEvent
}

/** Стан екрана: два незалежні прапорці + текст помилки. */
data class SplashState(
    val animationFinished: Boolean = false,
    val unpackFinished: Boolean = false,
    val error: String? = null,
) {
    /** Обидві умови завершено без помилки — можна іти на Home. */
    val bothDone: Boolean get() = isReady(animationFinished, unpackFinished, error)
}

/** Чистий редьюсер стану — покривається юніт-тестом [SplashViewModelTest]. */
fun reduceSplash(current: SplashState, event: SplashEvent): SplashState = when (event) {
    SplashEvent.AnimationFinished -> current.copy(animationFinished = true)
    SplashEvent.UnpackFinished -> current.copy(unpackFinished = true)
    is SplashEvent.UnpackFailed -> current.copy(error = event.message)
}

/** Таблиця істинності «обидві умови»: ready ⇔ аніма ∧ БД ∧ ¬помилка. */
fun isReady(animationFinished: Boolean, unpackFinished: Boolean, error: String?): Boolean =
    animationFinished && unpackFinished && error == null
