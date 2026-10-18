// AdManager.kt — інтерфейс-заглушка показу реклами (реальна реалізація — пізніше, ADMOB).
package dev.gurtom.core.ads

import javax.inject.Inject
import javax.inject.Singleton

/**
 * Точка входу для рекламних форматів. Наразі — заглушка: усі методи no-op,
 * щоб решта проєкту вже могла будуватися на стабільному контракті.
 */
@Singleton
class AdManager @Inject constructor(
    private val policy: AdPolicy,
) {

    /** Ініціалізація SDK; викликати один раз з Application.onCreate через DI. */
    suspend fun initialize() {
        if (!policy.adsEnabled) return
        // TODO: MobileAds.initialize(context)
    }

    /** Показ міжраундового інтерстишу, якщо політоя дозволяє. */
    suspend fun showInterstitial(onResult: (AdResult) -> Unit = {}) {
        if (!policy.canShowInterstitial()) {
            onResult(AdResult.SkippedByPolicy)
            return
        }
        // TODO: InterstitialAd.load + show
        onResult(AdResult.NotIntegratedYet)
    }

    /** Завантаження банера для нижньої частини екрана ігор. */
    suspend fun loadBanner(slotId: String): BannerHandle =
        BannerHandle(slotId)
}

/** Результат спроби показу реклами. */
sealed interface AdResult {
    data object Shown : AdResult
    data object Failed : AdResult
    data object SkippedByPolicy : AdResult
    data object NotIntegratedYet : AdResult
}

/** Дескриптор завантаженого банера; реальний view з'явиться з інтеграцією SDK. */
data class BannerHandle(val slotId: String)
