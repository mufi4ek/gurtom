// AdPolicy.kt — правила коли рекламу можна й не можна показувати.
package dev.gurtom.core.ads

import javax.inject.Inject
import javax.inject.Singleton

/**
 * Політика показу реклами: вікофільтр, оп-in користувача й частотний кап.
 * Заглушка читає лише консервативні значення за замовчуванням;
 * підключення до DataStore налаштувань — окремим етапом.
 */
@Singleton
class AdPolicy @Inject constructor() {

    /** Головний перемикач: false => жодного звернення до рекламного SDK. */
    val adsEnabled: Boolean = false

    /** Мінімальна кількість раундів між інтерстишіями (анти-fraud вимога PLAN). */
    val interstitialEveryNRounds: Int = 3

    private var roundsSinceLastInterstitial: Int = 0

    /** Чи можна зараз показати інтерстишій — частотний лічильник. */
    fun canShowInterstitial(): Boolean =
        adsEnabled && roundsSinceLastInterstitial >= interstitialEveryNRounds

    /** Викликати після кожного завершеного раунду гри. */
    fun onRoundFinished() {
        roundsSinceLastInterstitial++
    }

    /** Скидання лічильника одразу після успішного показу. */
    fun onInterstitialShown() {
        roundsSinceLastInterstitial = 0
    }
}
