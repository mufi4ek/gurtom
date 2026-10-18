// GurtomTheme.kt — єдина Material 3 тема застосунку (світла/темна динамічна).
package dev.gurtom.core.designsystem.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColors = lightColorScheme(
    primary = GurtomOrange,
    onPrimary = PaperSurface,
    primaryContainer = GurtomOrange.copy(alpha = 0.18f),
    background = PaperBackground,
    surface = PaperSurface,
    onBackground = InkText,
    onSurface = InkText,
)

private val DarkColors = darkColorScheme(
    primary = GurtomOrange,
    onPrimary = NightBackground,
    primaryContainer = GurtomOrangeDark,
    background = NightBackground,
    surface = NightSurface,
)

/**
 * Коренева тема Ґуртом: загортка над MaterialTheme із брендовою палітрою
 * та типографікою [GurtomTypography]. Усі екрани feature-модулів мають використовувати лише її.
 */
@Composable
fun GurtomTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = GurtomTypography,
        content = content,
    )
}
