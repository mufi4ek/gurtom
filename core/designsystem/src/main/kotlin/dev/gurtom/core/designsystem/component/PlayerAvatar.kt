// PlayerAvatar.kt — аватар гравця: 8 вбудованих емодзі-варіантів без мережі, коло surfaceVariant + акцентна обводка.
package dev.gurtom.core.designsystem.component

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/** 8 варіантів емодзі-аватарок (PLAN: без мережевих зображень). */
val GurtomAvatars = listOf("🦊", "🐼", "🐸", "🦉", "🐙", "🦄", "🐝", "🐳")

/** Круглий аватар; [variant] — індекс із [GurtomAvatars] (береться за модулем). */
@Composable
fun PlayerAvatar(
    variant: Int,
    modifier: Modifier = Modifier,
    selected: Boolean = false,
    size: Int = 48,
) {
    val scheme = MaterialTheme.colorScheme
    Box(
        modifier = modifier
            .size(size.dp)
            .background(scheme.surfaceVariant, CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        if (selected) {
            Box(
                modifier = Modifier
                    .size((size - 6).dp)
                    .background(scheme.primary.copy(alpha = 0.25f), CircleShape),
                contentAlignment = Alignment.Center,
            ) { AvatarEmoji(variant) }
        } else {
            AvatarEmoji(variant)
        }
    }
}

@Composable
private fun AvatarEmoji(variant: Int) {
    Text(
        text = GurtomAvatars[variant.mod(GurtomAvatars.size)],
        style = MaterialTheme.typography.headlineMedium,
    )
}
