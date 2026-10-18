// AccentColorPicker.kt — вибір акценту: 8 пресетів-кружків + власний колір через HSV ColorPicker (без залежностей).
package dev.gurtom.core.designsystem.component

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import dev.gurtom.core.designsystem.theme.AccentPreset
import dev.gurtom.core.designsystem.theme.MinTouchTarget
import kotlin.math.roundToInt

/**
 * Палітра акцентів: ряд із 8 кружків [AccentPreset] + повзунок відтінку для
 * власного кольору. Обраний варіант повертається через [onAccentChange].
 */
@Composable
fun AccentColorPicker(
    selected: Color,
    onAccentChange: (Color) -> Unit,
    modifier: Modifier = Modifier,
) {
    val scheme = MaterialTheme.colorScheme
    var hue by remember { mutableFloatStateOf(colorToHue(selected)) }
    Column(modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally),
        ) {
            AccentPreset.entries.forEach { preset ->
                val isSel = preset.color == selected
                Box(
                    modifier = Modifier
                        .size(MinTouchTarget)
                        .background(preset.color, CircleShape)
                        .border(
                            width = if (isSel) 3.dp else 1.dp,
                            color = if (isSel) scheme.onBackground else scheme.outline,
                            shape = CircleShape,
                        )
                        .clickable {
                            hue = colorToHue(preset.color)
                            onAccentChange(preset.color)
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    if (isSel) Text("✓", color = dev.gurtom.core.designsystem.theme.contrastSafe(preset.color, Color.Black))
                }
            }
        }
        Text("Власний відтінок", style = MaterialTheme.typography.labelMedium, color = scheme.onSurfaceVariant)
        Slider(
            value = hue,
            onValueChange = {
                hue = it
                onAccentChange(hsvToColor(it, 1f, 1f))
            },
            valueRange = 0f..360f,
        )
        Box(
            modifier = Modifier
                .size(MinTouchTarget)
                .background(hsvToColor(hue, 1f, 1f), CircleShape),
        )
    }
}

private fun colorToHue(c: Color): Float {
    val r = c.red; val g = c.green; val b = c.blue
    val max = maxOf(r, g, b); val min = minOf(r, g, b); val d = max - min
    if (d == 0f) return 0f
    val h = when (max) {
        r -> ((g - b) / d) % 6f
        g -> (b - r) / d + 2f
        else -> (r - g) / d + 4f
    } * 60f
    return (if (h < 0) h + 360 else h).roundToInt().coerceIn(0, 360).toFloat()
}

private fun hsvToColor(h: Float, s: Float, v: Float): Color {
    val c = v * s
    val x = c * (1 - ((h / 60f) % 2 - 1).let { if (it < 0) -it else it })
    val m = v - c
    val (r, g, b) = when {
        h < 60 -> Triple(c, x, 0f)
        h < 120 -> Triple(x, c, 0f)
        h < 180 -> Triple(0f, c, x)
        h < 240 -> Triple(0f, x, c)
        h < 300 -> Triple(x, 0f, c)
        else -> Triple(c, 0f, x)
    }
    return Color(r + m, g + m, b + m)
}
