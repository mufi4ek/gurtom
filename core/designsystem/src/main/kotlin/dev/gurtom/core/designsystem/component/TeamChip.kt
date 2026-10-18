// TeamChip.kt — чип команди: пілюля 999dp з назвою, рахунком і підсвіткою активної команди акцентом.
package dev.gurtom.core.designsystem.component

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import dev.gurtom.core.designsystem.theme.ChipShape
import dev.gurtom.core.designsystem.theme.MinTouchTarget
import dev.gurtom.core.designsystem.theme.contrastSafe

/** Компактний чип команди для лобі та рахунку. */
@Composable
fun TeamChip(
    name: String,
    modifier: Modifier = Modifier,
    score: Int = 0,
    active: Boolean = false,
) {
    val scheme = MaterialTheme.colorScheme
    val bg = if (active) scheme.primary else scheme.surfaceVariant
    val fg = if (active) contrastSafe(scheme.primary, scheme.surface) else scheme.onSurfaceVariant
    Row(
        modifier = modifier
            .defaultMinSize(minHeight = MinTouchTarget)
            .background(bg, ChipShape)
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(name, style = MaterialTheme.typography.labelMedium, color = fg)
        Text("$score", style = MaterialTheme.typography.labelMedium, color = fg.copy(alpha = 0.7f))
    }
}
