// TalkBackThrottleTest.kt — юніт-тест чистої логіки тротлінгу анонсів TimerRing (PLAN §7.4).
package dev.gurtom.core.designsystem.component

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Перевіряє, що анонси озвучуються лише на позначках 60/30/10/5/0 і не частіше ніж раз на 5 с. */
class TalkBackThrottleTest {

    @Test
    fun `перший анонс завжди проходить`() {
        assertTrue(shouldAnnounceTimer(remainingSeconds = 60, lastAnnounced = null))
        assertTrue(shouldAnnounceTimer(remainingSeconds = 47, lastAnnounced = null))
    }

    @Test
    fun `позначки анонсуються завжди`() {
        for (m in listOf(60, 30, 10, 5)) {
            assertTrue(shouldAnnounceTimer(m, lastAnnounced = m + 1))
        }
    }

    @Test
    fun `нуль анонсується один раз і не повторюється`() {
        assertTrue(shouldAnnounceTimer(0, lastAnnounced = 1))
        assertFalse(shouldAnnounceTimer(0, lastAnnounced = 0))
    }

    @Test
    fun `між позначками інтервал не менше 5 секунд`() {
        assertFalse(shouldAnnounceTimer(29, lastAnnounced = 30)) // 1 с — тихо
        assertFalse(shouldAnnounceTimer(28, lastAnnounced = 30)) // 2 с — тихо
        assertTrue(shouldAnnounceTimer(25, lastAnnounced = 30))  // рівно 5 с — можна
        assertTrue(shouldAnnounceTimer(20, lastAnnounced = 25))
    }

    @Test
    fun `повний раунд 60с дає не більше 14 анонсів замість 61`() {
        var last: Int? = null
        var announcements = 0
        for (s in 60 downTo 0) {
            if (shouldAnnounceTimer(s, last)) {
                announcements++
                last = s
            }
        }
        // 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0 => 13; вимога: значно менше за 61
        assertTrue(announcements <= 14)
    }
}
