// Color.kt — палітра Ґуртом: базові теми, 8 акцентних пресетів і WCAG-контраст (onAccent рахується, не захардкоджується).
package dev.gurtom.core.designsystem.theme

import androidx.compose.ui.graphics.Color
import kotlin.math.pow

/** Темний фон застосунку по замовчуванню. */
val DarkBackground = Color(0xFF0B0D10)

/** Темна поверхня карток і панелей. */
val DarkSurface = Color(0xFF12151A)

/** Темна варіантна поверхня (контейнери, чипи). */
val DarkSurfaceVariant = Color(0xFF1A1F26)

/** Темна лінія розмежування (outline). */
val DarkOutline = Color(0xFF2A3038)

/** Основний текст на темному фоні. */
val DarkOnBackground = Color(0xFFEAF0F6)

/** Додатковий текст/іконки у темній темі. */
val DarkOnSurfaceVariant = Color(0xFF9AA4B2)

/** Світлий фон застосунку. */
val LightBackground = Color(0xFFF7F8FA)

/** Біла поверхня у світлій темі. */
val LightSurface = Color(0xFFFFFFFF)

/** Світла варіантна поверхня. */
val LightSurfaceVariant = Color(0xFFEEF1F5)

/** Світла лінія розмежування. */
val LightOutline = Color(0xFFD6DBE2)

/** Основний текст на світлому фоні. */
val LightOnBackground = Color(0xFF101418)

/** Додатковий текст/іконки у світлій темі. */
val LightOnSurfaceVariant = Color(0xFF5A6472)

/** Стан «правильно» (спалах картки). */
val CorrectGreen = Color(0xFF39FF88)

/** Стан «помилково» (спалах картки). */
val WrongRed = Color(0xFFFF4D5E)

/**
 * Акцентні пресети користувача (PLAN §7.1): ім'я → насичений колір.
 * onAccent для кожного обчислюється функцією [contrastSafe], а не зберігається тут.
 */
enum class AccentPreset(val label: String, val color: Color) {
    NEON_GREEN("Neon Green", Color(0xFF39FF88)),
    CYAN("Cyan", Color(0xFF22E4FF)),
    MAGENTA("Magenta", Color(0xFFFF3CAC)),
    LIME("Lime", Color(0xFFC6FF3D)),
    AMBER("Amber", Color(0xFFFFB13D)),
    VIOLET("Violet", Color(0xFFA855F7)),
    RED("Red", Color(0xFFFF4D5E)),
    WHITE("White", Color(0xFFEAF0F6)),
}

/** Відносна яскравість за WCAG 2.1 (https://www.w3.org/TR/WCAG21/#relativeluminancedef). */
fun relativeLuminance(c: Color): Double {
    fun channel(v: Float): Double {
        val s = v.toDouble()
        return if (s <= 0.03928) s / 12.92 else ((s + 0.055) / 1.055).pow(2.4)
    }
    return 0.2126 * channel(c.red) + 0.7152 * channel(c.green) + 0.0722 * channel(c.blue)
}

/** Коефіцієнт контрасту двох кольорів за WCAG (1.0…21.0). */
fun contrastRatio(a: Color, b: Color): Double {
    val la = relativeLuminance(a)
    val lb = relativeLuminance(b)
    val hi = maxOf(la, lb)
    val lo = minOf(la, lb)
    return (hi + 0.05) / (lo + 0.05)
}

/**
 * Контрастний колір тексту/піктограм поверх [foreground] на фоні [background]:
 * повертає темний або світлий нейтраль, залежно від того, який дає ratio >= 4.5:1.
 * Якщо жоден суворий варіант не проходить (надзвичайно рідкісний випадок середніх тонів),
 * повертає варіант із максимальним контрастом.
 */
fun contrastSafe(foreground: Color, background: Color): Color {
    val dark = Color(0xFF0B0D10)
    val light = Color(0xFFEAF0F6)
    val rd = contrastRatio(foreground, dark)
    val rl = contrastRatio(foreground, light)
    return when {
        rd >= 4.5 -> dark
        rl >= 4.5 -> light
        rd >= rl -> dark
        else -> light
    }
}

/** Темний варіант акценту для світлої теми: затемнення, доки контраст з фоном не досягне 4.5:1. */
fun darkenUntilContrast(accent: Color, background: Color, target: Double = 4.5): Color {
    var c = accent
    var guard = 0
    while (contrastRatio(c, background) < target && guard < 40) {
        c = Color(c.red * 0.92f, c.green * 0.92f, c.blue * 0.92f, c.alpha)
        guard++
    }
    return c
}
