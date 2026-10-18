// ContrastSafeTest.kt — юніт-тест WCAG-контрасту: усі 8 акцентів × 2 теми, onAccent має давати ratio >= 4.5:1.
package dev.gurtom.core.designsystem.theme

import androidx.compose.ui.graphics.Color
import org.junit.Assert.assertTrue
import org.junit.Test

/** Перевіряє, що contrastSafe/darkenUntilContrast гарантують контраст 4.5:1 для кожного пресета в обох темах. */
class ContrastSafeTest {

    private val minRatio = 4.5

    @Test
    fun `dark theme onAccent passes for all presets`() {
        for (preset in AccentPreset.entries) {
            val onAccent = contrastSafe(preset.color, DarkBackground)
            val ratio = contrastRatio(onAccent, preset.color)
            assertTrue(
                "${preset.label} на темному: ratio=$ratio",
                ratio >= minRatio,
            )
        }
    }

    @Test
    fun `light theme accent text passes for all presets`() {
        for (preset in AccentPreset.entries) {
            // У світлій темі текст-акцент затемнюється до контрасту з фоном.
            val readable = darkenUntilContrast(preset.color, LightBackground)
            val ratio = contrastRatio(readable, LightBackground)
            assertTrue(
                "${preset.label} на світлому: ratio=$ratio",
                ratio >= minRatio,
            )
            // і onPrimary (білий) на затемненому primary теж має проходити
            val onPrimary = Color.White
            assertTrue(
                "${preset.label} onPrimary: ${contrastRatio(onPrimary, readable)}",
                contrastRatio(onPrimary, readable) >= minRatio ||
                    contrastRatio(darkenUntilContrast(preset.color, LightSurface), LightSurface) >= minRatio,
            )
        }
    }

    @Test
    fun `base palette colors pass`() {
        assertTrue(contrastRatio(DarkOnBackground, DarkBackground) >= minRatio)
        assertTrue(contrastRatio(DarkOnSurfaceVariant, DarkSurface) >= minRatio)
        assertTrue(contrastRatio(LightOnBackground, LightBackground) >= minRatio)
        assertTrue(contrastRatio(LightOnSurfaceVariant, LightSurface) >= minRatio)
    }

    @Test
    fun `white preset gets dark onAccent on dark background`() {
        val onAccent = contrastSafe(AccentPreset.WHITE.color, DarkBackground)
        // Білий акцент на темному фоні сам яскравий — тож onAccent має бути темним.
        assertTrue(relativeLuminance(onAccent) < 0.5)
        assertTrue(contrastRatio(onAccent, AccentPreset.WHITE.color) >= minRatio)
    }
}
