// AutoSizeText.kt — GurtomAutoSizeText і Modifier.autoSizeText: текст сам зменшує розмір шрифту (96/72/56/40), доки не влізе у maxLines рядків (вимірювання TextMeasurer + підтвердження onTextLayout).
package dev.gurtom.core.designsystem.component

import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.layout.onTextLayout
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.sp

/** Базовий стек розмірів для слова в грі (PLAN §7.2 autoSize-варіанти 96/72/56/40). */
val GurtomAutoSizes = listOf(96.sp, 72.sp, 56.sp, 40.sp, 32.sp)

/**
 * Вимірює [text] TextMeasurer'ом для кожного розміру зі стека [sizes] (від найбільшого)
 * і повертає індекс першого розміру, за якого текст вміщується у [maxLines] рядків
 * та у ширину [widthPx]. Використовується [GurtomAutoSizeText].
 */
@Composable
fun rememberAutoSizeIndex(
    text: String,
    style: TextStyle,
    sizes: List<TextUnit>,
    maxLines: Int,
    widthPx: Int,
): Int {
    val measurer = rememberTextMeasurer()
    val density = LocalDensity.current
    return remember(text, style.fontWeight, style.fontFamily, sizes, maxLines, widthPx, density.density) {
        var chosen = sizes.lastIndex
        val maxWidth = if (widthPx > 0) widthPx else Constraints.MaxWidth
        for (i in sizes.indices) {
            val s = style.copy(fontSize = sizes[i])
            val layout = measurer.measure(
                text = text,
                style = s,
                constraints = Constraints(maxWidth = maxWidth),
            )
            if (layout.lineCount <= maxLines) {
                chosen = i
                break
            }
        }
        chosen
    }
}

/**
 * Текст-«слово в грі», що автомасштабується: послідовно зменшує fontSize зі стека
 * [sizes], доки текст не влізе у [maxLines] рядки доступної ширини. Факт розкладання
 * additionally підтверджується через onTextLayout (захист від edge-case переповнення).
 */
@Composable
fun GurtomAutoSizeText(
    text: String,
    modifier: Modifier = Modifier,
    style: TextStyle = LocalTextStyle.current,
    sizes: List<TextUnit> = GurtomAutoSizes,
    maxLines: Int = 2,
    textAlign: TextAlign = TextAlign.Center,
) {
    var boxWidthPx by remember(text) { mutableIntStateOf(0) }
    var overflowHappened by remember(text) { mutableStateOf(false) }
    val measured = rememberAutoSizeIndex(text, style, sizes, maxLines, boxWidthPx)
    val index = if (overflowHappened && measured < sizes.lastIndex) measured + 1 else measured
    Box(
        modifier = modifier
            .fillMaxWidth()
            .onSizeChanged { s: IntSize -> if (s.width != boxWidthPx) boxWidthPx = s.width },
    ) {
        Text(
            text = text,
            modifier = Modifier.onTextLayout { layout ->
                if (layout.didOverflowHeight || layout.lineCount > maxLines) {
                    if (!overflowHappened) overflowHappened = true
                }
            },
            style = style.copy(fontSize = sizes[index]),
            maxLines = maxLines,
            textAlign = textAlign,
        )
    }
}
