// HapticsManager.kt — централізоване керування вібрацією (використовує дозвіл VIBRATE).
package dev.gurtom.core.common.haptics

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Менеджер тактильного відгуку: короткі імпульси для подій гри (переворот картки,
 * таймер, вгадане слово). Мовчить, якщо пристрій не має вібросигналу.
 */
@Singleton
class HapticsManager @Inject constructor(
    @ApplicationContext private val context: Context,
) {

    private val vibrator: Vibrator? by lazy {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            context.getSystemService(VibratorManager::class.java)?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Vibrator::class.java)
        }?.takeIf { it.hasVibrator() }
    }

    /** Легкий «тап» — 12 мс. */
    fun tap() = pulse(12)

    /** Середній імпульс — підтвердження дії, 24 мс. */
    fun confirm() = pulse(24)

    /** Подвійний імпульс — кінець раунду / сплив таймера. */
    fun doubleBuzz() {
        val v = vibrator ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            v.vibrate(VibrationEffect.createOneShot(30, VibrationEffect.DEFAULT_AMPLITUDE))
            v.vibrate(VibrationEffect.createOneShot(60, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            v.vibrate(60)
        }
    }

    private fun pulse(ms: Long) {
        val v = vibrator ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            v.vibrate(VibrationEffect.createOneShot(ms, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            v.vibrate(ms)
        }
    }
}
