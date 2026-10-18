// TimerRing.kt — кільцевий таймер на Canvas drawArc: progress 0..1, warnBelow — останні секунди (пульсація 1 Гц + колір error).
package dev.gurtom.core.designsystem.component

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import dev.gurtom.core.designsystem.theme.GurtomMotion
import dev.gurtom.core.designsystem.theme.LocalReducedMotion
import dev.gurtom.core.designsystem.theme.MinTouchTarget
import kotlin.math.min

/**
 * Кільце прогресу часу гри. [progress] — частка, що залишилася (1 → 0).
 * Коли progress <= [warnBelow] — дуга стає кольору error і пульсує з частотою 1 Гц
 * (вимкнено, якщо LocalReducedMotion == true). Має semantics liveRegion для TalkBack.
 */
@Composable
fun TimerRing(
    progress: Float,
    modifier: Modifier = Modifier,
    warnBelow: Float = 1f / 6f,
    totalSeconds: Int = 60,
) {
    val scheme = MaterialTheme.colorScheme
    val reduced = LocalReducedMotion.current
    val warning = progress <= warnBelow
    val transition = rememberInfiniteTransition(label = "timerPulse")
    val pulse by transition.animateFloat(
        initialValue = 0.55f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(GurtomMotion.TIMER_PULSE_PERIOD_MS.toInt(), easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "timerPulseAlpha",
    )
    val trackColor = scheme.surfaceVariant
    val activeColor = if (warning) scheme.error else scheme.primary
    val strokeWidth = 12.dp
    // Тротлінг TalkBack: оновлюємо contentDescription лише на позначках 60/30/10/5/0
    // або не частіше ніж раз на 5 с (чиста функція shouldAnnounceTimer).
    val remaining = ceilToInt(progress * totalSeconds)
    var lastAnnounced by remember(totalSeconds) { mutableIntStateOf(remaining) }
    var announcedText by remember(totalSeconds) { mutableStateOf("Таймер: $remaining с") }
    LaunchedEffect(remaining) {
        if (shouldAnnounceTimer(remaining, lastAnnounced)) {
            lastAnnounced = remaining
            announcedText = "Таймер: $remaining с"
        }
    }
    Box(
        modifier = modifier
            .defaultMinSize(MinTouchTarget, MinTouchTarget)
            .size(160.dp)
            .semantics {
                contentDescription = announcedText
                liveRegion = LiveRegionMode.Polite
            },
        contentAlignment = Alignment.Center,
    ) {
        Canvas(modifier = Modifier.matchParentSize()) {
            val stroke = strokeWidth.toPx()
            val d = min(size.width, size.height) - stroke
            val topLeft = (size.width - d) / 2f
            val topOffset = (size.height - d) / 2f
            // Доріжка
            drawArc(
                color = trackColor,
                startAngle = -90f,
                sweepAngle = 360f,
                useCenter = false,
                topLeft = androidx.compose.ui.geometry.Offset(topLeft, topOffset),
                size = Size(d, d),
                style = Stroke(width = stroke, cap = StrokeCap.Round),
            )
            // Прогрес
            drawArc(
                color = if (warning && !reduced) activeColor.copy(alpha = pulse) else activeColor,
                startAngle = -90f,
                sweepAngle = 360f * progress.coerceIn(0f, 1f),
                useCenter = false,
                topLeft = androidx.compose.ui.geometry.Offset(topLeft, topOffset),
                size = Size(d, d),
                style = Stroke(width = stroke, cap = StrokeCap.Round),
            )
        }
    }
}

private fun ceilToInt(x: Float): Int = Math.ceil(x.toDouble()).toInt().coerceAtLeast(0)
