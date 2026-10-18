// HomeScreen.kt — екран-home (заглушка скелета): назва + кнопка «Назад».
package dev.gurtom.feature.home

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import dev.gurtom.core.designsystem.component.ScreenScaffold

/**
 * Заглушка екрана «Home». Повноцінний UI з'явиться в наступних ітераціях;
 * зараз лише контракт навігації: показуємо назву й даємо можливість повернутися.
 */
@Composable
fun HomeScreen(onBack: () -> Unit, modifier: Modifier = Modifier) {
    ScreenScaffold(title = stringResource(R.string.home_screen_title), onBack = onBack, modifier = modifier)
}
