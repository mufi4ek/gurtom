// GurtomIconButton.kt — іконкова кнопка Ґуртом з мінімальною зоною тапу 48dp та contentDescription для доступності.
package dev.gurtom.core.designsystem.component

import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import dev.gurtom.core.designsystem.theme.MinTouchTarget

/** Кругла іконкова кнопка; [contentDescription] обов'язкова (TalkBack). */
@Composable
fun GurtomIconButton(
    icon: ImageVector,
    contentDescription: String?,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    IconButton(
        onClick = onClick,
        modifier = modifier.defaultMinSize(MinTouchTarget, MinTouchTarget),
        enabled = enabled,
        colors = IconButtonDefaults.iconButtonColors(
            contentColor = MaterialTheme.colorScheme.primary,
        ),
    ) {
        Icon(imageVector = icon, contentDescription = contentDescription)
    }
}
