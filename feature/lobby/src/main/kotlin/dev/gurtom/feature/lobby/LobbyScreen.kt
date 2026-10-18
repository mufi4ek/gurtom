// LobbyScreen.kt — екран-lobby (заглушка скелета): назва + кнопка «Назад».
package dev.gurtom.feature.lobby

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import dev.gurtom.core.designsystem.component.ScreenScaffold

/**
 * Заглушка екрана «Lobby». Повноцінний UI з'явиться в наступних ітераціях;
 * зараз лише контракт навігації: показуємо назву й даємо можливість повернутися.
 */
@Composable
fun LobbyScreen(onBack: () -> Unit, modifier: Modifier = Modifier) {
    ScreenScaffold(title = stringResource(R.string.lobby_screen_title), onBack = onBack, modifier = modifier)
}
