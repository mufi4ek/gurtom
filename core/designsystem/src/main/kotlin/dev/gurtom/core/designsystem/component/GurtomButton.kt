// GurtomButton.kt — кнопка Ґуртом: primary/secondary/tonal/ghost/text із зоною тапу >= 48dp і контрастним onAccent.
package dev.gurtom.core.designsystem.component

import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import dev.gurtom.core.designsystem.theme.MinTouchTarget
import dev.gurtom.core.designsystem.theme.contrastSafe

/** Variantи кнопки Ґуртом. */
enum class GurtomButtonVariant { PRIMARY, SECONDARY, TONAL, GHOST, TEXT }

/**
 * Єдина кнопка застосунку. PRIMARY заповнюється акцентом теми, текст — contrastSafe(accent, surface),
 * тож контраст >= 4.5:1 у будь-якій темі й при будь-якому акценті.
 */
@Composable
fun GurtomButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    variant: GurtomButtonVariant = GurtomButtonVariant.PRIMARY,
    enabled: Boolean = true,
) {
    val accent = MaterialTheme.colorScheme.primary
    val onAccent = if (variant == GurtomButtonVariant.PRIMARY || variant == GurtomButtonVariant.TONAL) {
        contrastSafe(accent, MaterialTheme.colorScheme.surface)
    } else {
        MaterialTheme.colorScheme.onSurface
    }
    val minSize = Modifier.defaultMinSize(minHeight = MinTouchTarget, minWidth = 64.dp)
    when (variant) {
        GurtomButtonVariant.PRIMARY -> Button(
            onClick = onClick,
            modifier = modifier.then(minSize),
            shape = MaterialTheme.shapes.small,
            colors = ButtonDefaults.buttonColors(
                containerColor = accent,
                contentColor = onAccent,
                disabledContainerColor = Color.Gray.copy(alpha = 0.3f),
            ),
            enabled = enabled,
        ) { Text(text, style = MaterialTheme.typography.labelMedium) }

        GurtomButtonVariant.SECONDARY -> OutlinedButton(
            onClick = onClick,
            modifier = modifier.then(minSize),
            shape = MaterialTheme.shapes.small,
            colors = ButtonDefaults.outlinedButtonColors(contentColor = accent),
            enabled = enabled,
        ) { Text(text, style = MaterialTheme.typography.labelMedium) }

        GurtomButtonVariant.TONAL -> Button(
            onClick = onClick,
            modifier = modifier.then(minSize),
            shape = MaterialTheme.shapes.small,
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer,
                contentColor = onAccent,
            ),
            enabled = enabled,
        ) { Text(text, style = MaterialTheme.typography.labelMedium) }

        GurtomButtonVariant.GHOST, GurtomButtonVariant.TEXT -> TextButton(
            onClick = onClick,
            modifier = modifier.then(minSize),
            shape = MaterialTheme.shapes.small,
            colors = ButtonDefaults.textButtonColors(contentColor = accent),
            enabled = enabled,
        ) { Text(text, style = MaterialTheme.typography.labelMedium) }
    }
}
