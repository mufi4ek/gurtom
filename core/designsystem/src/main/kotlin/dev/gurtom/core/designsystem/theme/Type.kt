// Type.kt — типографіка Material 3 для екранів ігор (великі «кепглі»-слова).
package dev.gurtom.core.designsystem.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * друкована типографіка застосунку: базова M3 + власний стиль [displayWord]
 * для показу слова на весь екран (Аліас, Крокодил, Хто я?).
 */
val GurtomTypography: Typography = Typography().apply {
    titleLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 28.sp,
        lineHeight = 34.sp,
    )
    labelLarge = TextStyle(
        fontWeight = FontWeight.SemiBold,
        fontSize = 14.sp,
        letterSpacing = 0.1.sp,
    )
}

/** Стиль самого слова-картки: максимально великий, по центру. */
val displayWordStyle: TextStyle = TextStyle(
    fontFamily = FontFamily.Serif,
    fontWeight = FontWeight.Black,
    fontSize = 48.sp,
    lineHeight = 56.sp,
)
