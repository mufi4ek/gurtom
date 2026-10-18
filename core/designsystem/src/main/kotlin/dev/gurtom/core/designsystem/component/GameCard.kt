// GameCard.kt — велика картка зі словом: стани idle/flashCorrect/flashWrong/paused, autoSize-слово, коректний контраст у будь-якій темі.
package dev.gurtom.core.designsystem.component

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import dev.gurtom.core.designsystem.theme.GurtomMotion
import dev.gurtom.core.designsystem.theme.LocalReducedMotion
import dev.gurtom.core.designsystem.theme.contrastSafe

/** Стан карти зі словом. */
enum class GameCardState { IDLE, FLASH_CORRECT, FLASH_WRONG, PAUSED }

/**
 * Картка гри: слово на весь екран (GurtomAutoSizeText 96/72/56/40), спалах
 * «вгадало/не вгадав» зі scale-пружиною GurtomMotion.cardSpring; текст завжди
 * contrastSafe відносно фону картки.
 */
@Composable
fun GameCard(
    word: String,
    modifier: Modifier = Modifier,
    state: GameCardState = GameCardState.IDLE,
) {
    val scheme = MaterialTheme.colorScheme
    val reduced = LocalReducedMotion.current
    val bg = when (state) {
        GameCardState.FLASH_CORRECT -> scheme.primary
        GameCardState.FLASH_WRONG -> scheme.error
        else -> scheme.surfaceVariant
    }
    val fg = contrastSafe(bg, scheme.surface)
    val pop by animateFloatAsState(
        targetValue = if (!reduced && state == GameCardState.FLASH_CORRECT) 1.06f else 1f,
        animationSpec = GurtomMotion.cardSpring(),
        label = "gameCardScale",
    )
    Box(
        modifier = modifier
            .fillMaxWidth()
            .background(bg, shape = RoundedCornerShape(16.dp))
            .scale(pop)
            .padding(24.dp),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            GurtomAutoSizeText(
                text = word,
                style = MaterialTheme.typography.displayLarge.copy(color = fg),
                textAlign = TextAlign.Center,
            )
            if (state == GameCardState.PAUSED) {
                Text(
                    text = "⏸",
                    style = MaterialTheme.typography.headlineMedium,
                    color = fg,
                    modifier = Modifier.padding(top = 16.dp),
                )
            }
        }
    }
}
