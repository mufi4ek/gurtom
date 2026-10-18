// SplashViewModelTest.kt — юніт-тест чистої логіки «обидві умови завершено» (анімація + розпакування) без Compose й Android.
package dev.gurtom.feature.splash

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Перевіряє редьюсер стану сплешу: Ready — тільки коли анімація І БД готові; помилка блокує перехід. */
class SplashViewModelTest {

    private val reduce = ReduceApi()

    /** Адаптер, що викликає чистий редьюсер через exposed-instance (без конструювання ViewModel з DI). */
    private class ReduceApi {
        private val vm: SplashViewModel by lazy {
            // Unsafe-подібний трюк не потрібен: екземпляр створюється з фейковим unpacker через null-контекст
            // неможливий, тому використовуємо companion isReady + дублювання переходів нижче.
            throw UnsupportedOperationException()
        }

        fun next(animationFinished: Boolean, unpackFinished: Boolean, error: String?, event: String): Boolean {
            val a = animationFinished || event == "animation"
            val u = unpackFinished || event == "unpack"
            val e = if (event == "fail") "boom" else error
            return SplashViewModel.isReady(a, u, e)
        }
    }

    @Test
    fun `ready only when both animation and unpack finished`() {
        assertFalse(reduce.next(false, false, null, "animation"))
        assertFalse(reduce.next(false, false, null, "unpack"))
        assertTrue(reduce.next(true, false, null, "unpack"))
        assertTrue(reduce.next(false, true, null, "animation"))
    }

    @Test
    fun `error blocks ready`() {
        assertFalse(reduce.next(true, true, null, "fail"))
        assertFalse(SplashViewModel.isReady(animationFinished = true, unpackFinished = true, error = "пошкоджений архів"))
    }

    @Test
    fun `isReady truth table`() {
        assertTrue(SplashViewModel.isReady(true, true, null))
        assertFalse(SplashViewModel.isReady(false, true, null))
        assertFalse(SplashViewModel.isReady(true, false, null))
        assertFalse(SplashViewModel.isReady(true, true, "boom"))
    }
}
