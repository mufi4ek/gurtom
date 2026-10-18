// Motion.kt — специфікації руху Ґуртом (GurtomMotion) і CompositionLocal зменшеного руху (LocalReducedMotion).
package dev.gurtom.core.designsystem.theme

import android.provider.Settings
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.runtime.Composable
import androidx.compose.runtime.ProvidableCompositionLocal
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView

/**
 * Токени анімацій застосунку: пружини карток, фліпи 3D, stagger списків, спалахи станів.
 * Усі feature-модулі беруть тривалості/криві лише звідси.
 */
object GurtomMotion {
    /** Пружина для карток і панелей: stiffness 380, dampingRatio 0.82. */
    fun <T : Any> cardSpring() = spring<T>(dampingRatio = 0.82f, stiffness = 380f)

    /** Фліп карти «Правда/Дія»: 320 ms FastOutSlowIn. */
    fun <T : Any> flipTween() = tween<T>(durationMillis = 320, easing = FastOutSlowInEasing)

    /** Перехід між екранами/іграми. */
    fun <T : Any> screenFade() = tween<T>(durationMillis = 320, easing = FastOutSlowInEasing)

    /** Спалах «вгадало»: 120 ms. */
    fun <T : Any> flashSpec() = tween<T>(durationMillis = 120, easing = FastOutSlowInEasing)

    /** Затримка появи елементів списку. */
    const val STAGGER_MS = 60L

    /** Пульсація таймера в останні 10 с — 1 Гц. */
    const val TIMER_PULSE_PERIOD_MS = 1000L
}

/**
 * Чи следует зменшувать анімації: системний прапорець анімувань
 * (window animation scale / TRANSITION_ANIMATION_SCALE) АБО користувацький
 * перемикач «Зменшити рух» у налаштуваннях (надається вище по дереву Compose).
 */
@Composable
fun rememberReducedMotion(userPrefersReducedMotion: Boolean = false): Boolean {
    if (userPrefersReducedMotion) return true
    val context = LocalContext.current
    val viewScale = LocalView.current.windowAnimationScale
    val transitionScale = Settings.Global.getFloat(
        context.contentResolver,
        Settings.Global.TRANSITION_ANIMATION_SCALE,
        1f,
    )
    return viewScale < 0.15f || transitionScale < 0.15f
}

/** CompositionLocal прапорця зменшеного руху; за замовчуванням — увімкнено, доки тема не надасть значення. */
val LocalReducedMotion: ProvidableCompositionLocal<Boolean> =
    staticCompositionLocalOf { true }
