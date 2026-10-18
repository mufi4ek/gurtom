// Previews.kt — прев'ю всіх компонентів дизайн-системи: темна й світла тема × акцентні пресети.
package dev.gurtom.core.designsystem.component

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import dev.gurtom.core.designsystem.theme.AccentPreset
import dev.gurtom.core.designsystem.theme.GurtomTheme

@Composable
private fun Showcase(dark: Boolean, accent: AccentPreset = AccentPreset.NEON_GREEN) {
    GurtomTheme(darkTheme = dark, accent = accent.color) {
        Surface(color = MaterialTheme.colorScheme.background) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                GurtomTopAppBar(title = "Ґуртом", onBack = {})
                SectionHeader("Кнопки")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    GurtomButton("Primary", onClick = {})
                    GurtomButton("Ghost", onClick = {}, variant = GurtomButtonVariant.GHOST)
                    GurtomIconButton(icon = Icons.Filled.Check, contentDescription = "Ок", onClick = {})
                }
                GameCard(word = "хтось-небудь", modifier = Modifier.fillMaxWidth().padding(vertical = 24.dp))
                Text("Тема: ${if (dark) "темна" else "світла"} · ${accent.label}", style = MaterialTheme.typography.bodyLarge)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TeamChip("Гагаузи", score = 12, active = true)
                    TeamChip("Бульбаши", score = 9)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    PlayerAvatar(0, selected = true)
                    PlayerAvatar(3)
                    PlayerAvatar(7)
                }
                TimerRing(progress = 0.12f)
                SettingsSwitch(title = "Зменшити рух", checked = false, onCheckedChange = {})
                AccentColorPicker(selected = accent.color, onAccentChange = {})
                EmptyState("Поки що порожньо", description = "Створіть першу кімнату")
                ErrorState("Не вдалося завантажити словник", onRetry = {})
            }
        }
    }
}

@Preview(name = "Showcase Dark", showBackground = true)
@Composable private fun PreviewDark() = Showcase(dark = true)

@Preview(name = "Showcase Light", showBackground = true)
@Composable private fun PreviewLight() = Showcase(dark = false)

@Preview(name = "Accents Dark grid", showBackground = true)
@Composable
private fun PreviewAccents() {
    // Прев'ю кожного з 8 акцентів у темній темі по колу.
    GurtomTheme(darkTheme = true, accent = AccentPreset.MAGENTA.color) {
        Surface(color = MaterialTheme.colorScheme.background, modifier = Modifier.fillMaxSize()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                AccentPreset.entries.forEach { preset ->
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
                    ) {
                        GurtomTheme(darkTheme = true, accent = preset.color) {
                            GurtomButton(preset.label, onClick = {})
                            GameCard(word = "слово", modifier = Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}

@Preview(name = "GameCard states Dark", showBackground = true)
@Composable
private fun PreviewCardStatesDark() {
    GurtomTheme(darkTheme = true) {
        Surface(color = MaterialTheme.colorScheme.background) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                GameCard("вгадай", state = GameCardState.FLASH_CORRECT)
                GameCard("нічого", state = GameCardState.FLASH_WRONG)
                GameCard("пауза", state = GameCardState.PAUSED)
            }
        }
    }
}

@Preview(name = "GameCard states Light", showBackground = true)
@Composable
private fun PreviewCardStatesLight() {
    GurtomTheme(darkTheme = false) {
        Surface(color = MaterialTheme.colorScheme.background) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                GameCard("вгадай", state = GameCardState.FLASH_CORRECT)
                GameCard("нічого", state = GameCardState.FLASH_WRONG)
            }
        }
    }
}
