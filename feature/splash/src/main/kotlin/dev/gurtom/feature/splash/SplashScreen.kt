// SplashScreen.kt — екран-splash (заглушка скелета): назва + кнопка «Назад».
package dev.gurtom.feature.splash

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import dev.gurtom.core.designsystem.component.ScreenScaffold

/**
 * Заглушка екрана «Splash». Повноцінний UI з'явиться в наступних ітераціях;
 * зараз лише контракт навігації: показуємо назву й даємо можливість повернутися.
 */
@Composable
fun SplashScreen(onBack: () -> Unit, modifier: Modifier = Modifier) {
    ScreenScaffold(title = stringResource(R.string.splash_screen_title), onBack = onBack, modifier = modifier)
}
