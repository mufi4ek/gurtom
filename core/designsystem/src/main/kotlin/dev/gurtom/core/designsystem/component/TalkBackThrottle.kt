// TalkBackThrottle.kt — чиста (поза Compose) логіка тротлінгу анонсів таймера для TalkBack:
// анонсувати залишок часу лише на позначках 60/30/10/5 с і на нулі, не частіше ніж раз на 5 секунд.
package dev.gurtom.core.designsystem.component

/**
 * Ключем є повний залишок часу в секундах; значенням — чи є ця секунда «позначкою»,
 * яку варто озвучити асистивному зчитувачу (PLAN §7.4, доступність TimerRing).
 */
val TimerAnnounceMilestones: Set<Int> = setOf(60, 30, 10, 5, 0)

/**
 * Визначає, чи потрібно оновити contentDescription таймера для поточного [remainingSeconds]
 * відносно останнього анонсованого значення [lastAnnounced].
 *
 * Правила:
 *  - перший анонс (lastAnnounced == null) — завжди;
 *  - нуль (кінець раунду) — завжди;
 *  - позначки 60/30/10/5 с — завжди;
 *  - усе інше — лише якщо з останнього анонсу минуло >= [MIN_INTERVAL_SECONDS] (5 с),
 *    щоб не спамити TalkBack щосекунди.
 */
fun shouldAnnounceTimer(remainingSeconds: Int, lastAnnounced: Int?): Boolean {
    if (lastAnnounced == null) return true
    if (remainingSeconds <= 0) return lastAnnounced > 0
    if (remainingSeconds in TimerAnnounceMilestones) return remainingSeconds != lastAnnounced
    return lastAnnounced - remainingSeconds >= MIN_INTERVAL_SECONDS
}

private const val MIN_INTERVAL_SECONDS = 5
