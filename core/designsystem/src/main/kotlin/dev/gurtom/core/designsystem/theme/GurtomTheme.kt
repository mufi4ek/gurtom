// GurtomTheme.kt — коренева тема Ґуртом: MaterialTheme + власна ColorScheme, акцент як CompositionLocal (LocalAccentColor) без реконструкції Activity.
package dev.gurtom.core.designsystem.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.ProvidableCompositionLocal
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

/** Локальний акцентний колір: змінюється в рантаймі без перестворення Activity. */
val LocalAccentColor: ProvidableCompositionLocal<Color> =
    staticCompositionLocalOf { AccentPreset.NEON_GREEN.color }

private fun darkScheme(accent: Color) = darkColorScheme(
    primary = accent,
    onPrimary = contrastSafe(accent, DarkSurface),
    primaryContainer = accent.copy(alpha = 0.24f),
    onPrimaryContainer = accent,
    background = DarkBackground,
    onBackground = DarkOnBackground,
    surface = DarkSurface,
    onSurface = DarkOnBackground,
    surfaceVariant = DarkSurfaceVariant,
    onSurfaceVariant = DarkOnSurfaceVariant,
    outline = DarkOutline,
    outlineVariant = DarkOutline.copy(alpha = 0.5f),
    error = WrongRed,
    onError = contrastSafe(WrongRed, DarkSurface),
    scrim = Color.Black,
)

private fun lightScheme(accent: Color) = lightColorScheme(
    // На світлому фоні яскравий неон затемнюємо до контрасту >= 4.5:1 (PLAN §7.4).
    primary = darkenUntilContrast(accent, LightBackground),
    onPrimary = Color.White,
    primaryContainer = accent.copy(alpha = 0.18f),
    onPrimaryContainer = darkenUntilContrast(accent, LightBackground),
    background = LightBackground,
    onBackground = LightOnBackground,
    surface = LightSurface,
    onSurface = LightOnBackground,
    surfaceVariant = LightSurfaceVariant,
    onSurfaceVariant = LightOnSurfaceVariant,
    outline = LightOutline,
    outlineVariant = LightOutline.copy(alpha = 0.6f),
    error = darkenUntilContrast(WrongRed, LightBackground),
    onError = Color.White,
    scrim = Color.Black,
)

/**
 * Корінь дизайн-системи: темна база за замовчуванням, [accent] — параметр
 * (один із 8 пресетів або власний колір). onAccent рахується через [contrastSafe].
 * Надає [LocalAccentColor], [LocalSpacing], [LocalReducedMotion], форми й типографіку.
 */
@Composable
fun GurtomTheme(
    darkTheme: Boolean = true,
    accent: Color = AccentPreset.NEON_GREEN.color,
    userPrefersReducedMotion: Boolean = false,
    content: @Composable () -> Unit,
) {
    val colorScheme = remember(darkTheme, accent) {
        if (darkTheme) darkScheme(accent) else lightScheme(accent)
    }
    val reduced = rememberReducedMotion(userPrefersReducedMotion)
    CompositionLocalProvider(
        LocalAccentColor provides accent,
        LocalSpacing provides GurtomSpacing,
        LocalReducedMotion provides reduced,
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = GurtomTypography,
            shapes = GurtomShapes,
            content = content,
        )
    }
}
