// Shape.kt — кути та сітка відступів дизайн-системи Ґуртом (PLAN §7, мінімальна зона тапу 48dp).
package dev.gurtom.core.designsystem.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.unit.dp

/** Кути: картки 16dp, кнопки 12dp, чипи — «пілюля» 999dp. */
val GurtomShapes = Shapes(
    extraSmall = RoundedCornerShape(8.dp),
    small = RoundedCornerShape(12.dp),      // кнопки
    medium = RoundedCornerShape(16.dp),     // картки
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(24.dp),
)

/** Форма чипа — повна пілюля. */
val ChipShape = RoundedCornerShape(999.dp)

/** Крок сітки відступів: 4/8/12/16/24/32 dp. */
data class Spacing(val all: androidx.compose.ui.unit.Dp) {
    val xs = 4.dp
    val s = 8.dp
    val m = 12.dp
    val l = 16.dp
    val xl = 24.dp
    val xxl = 32.dp
}

/** Глобальний об'єкт відступів; доступний через [LocalSpacing]. */
val GurtomSpacing = Spacing(0.dp)

/** Мінімальна зона тапу для будь-якої інтерактивної області. */
val MinTouchTarget = 48.dp

/** CompositionLocal сітки відступів. */
val LocalSpacing = staticCompositionLocalOf { GurtomSpacing }
