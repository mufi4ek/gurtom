// SplashViewModel.kt — стан сплешу «Ґуртом»: паралельно чекає завершення анімації лога і розпакування БД; перехід на Home лише коли обидві умови виконані (PLAN §4.2, DATA_SCHEMA §1).
package dev.gurtom.feature.splash

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dev.gurtom.core.database.unpack.WordDatabaseAssetUnpacker
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * Логіка готовності сплешу. Тестована частина — чистий редьюсер [reduce],
 * який не залежить від Compose/Android: події AnimationFinished та UnpackFinished
 * перемикають стан у Ready тільки коли обидва прапорці встановлені.
 */
@HiltViewModel
class SplashViewModel @Inject constructor(
    private val unpacker: WordDatabaseAssetUnpacker,
) : ViewModel() {

    /** Фази екрана: анімація + розпакування йдуть паралельно, потім Ready або Error. */
    sealed interface Phase {
        data object Running : Phase
        data object Ready : Phase
        data class Failed(val message: String) : Phase
    }

    /** Внутрішній стан: два незалежні прапорці + помилка. */
    data class State(
        val animationFinished: Boolean = false,
        val unpackFinished: Boolean = false,
        val error: String? = null,
    ) {
        /** Обидві умови завершено — можна іти на Home. */
        val bothDone: Boolean get() = animationFinished && unpackFinished && error == null
    }

    private val _state = MutableStateFlow(State())
    val state: StateFlow<State> = _state.asStateFlow()

    /** Чистий редьюсер (без Android-залежностей) — покривається юніт-тестом. */
    fun reduce(current: State, event: Event): State = when (event) {
        Event.AnimationFinished -> current.copy(animationFinished = true)
        Event.UnpackFinished -> current.copy(unpackFinished = true)
        is Event.UnpackFailed -> current.copy(error = event.message)
    }

    /** Події стану сплешу. */
    sealed interface Event {
        data object AnimationFinished : Event
        data object UnpackFinished : Event
        data class UnpackFailed(val message: String) : Event
    }

    fun onEvent(event: Event) {
        _state.update { reduce(it, event) }
    }

    /** Запускає розпакування на IO (через unpacker); не блокує Main. */
    fun startUnpacking() {
        viewModelScope.launch {
            runCatching { unpacker.ensureUnpacked() }
                .onSuccess { onEvent(Event.UnpackFinished) }
                .onFailure { t -> onEvent(Event.UnpackFailed(t.message ?: "Не вдалося підготувати словник")) }
        }
    }

    /** Повтор після помилки: скидаємо прапорці розпакування і знову ensureUnpacked(). */
    fun retryUnpacking() {
        _state.update { it.copy(unpackFinished = false, error = null) }
        startUnpacking()
    }

    companion object {
        /** Готовий чи ні — чиста функція для тестів «обидві умови завершено». */
        fun isReady(animationFinished: Boolean, unpackFinished: Boolean, error: String?): Boolean =
            animationFinished && unpackFinished && error == null
    }
}
