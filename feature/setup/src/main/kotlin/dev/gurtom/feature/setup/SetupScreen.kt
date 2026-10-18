// SetupScreen.kt — екран-setup (заглушка скелета): назва + кнопка «Назад».
package dev.gurtom.feature.setup

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import dev.gurtom.core.designsystem.component.ScreenScaffold

/**
 * Заглушка екрана «Setup». Повноцінний UI з'явиться в наступних ітераціях;
 * зараз лише контракт навігації: показуємо назву й даємо можливість повернутися.
 */
@Composable
fun SetupScreen(onBack: () -> Unit, modifier: Modifier = Modifier) {
    ScreenScaffold(title = stringResource(R.string.setup_screen_title), onBack = onBack, modifier = modifier)
}
