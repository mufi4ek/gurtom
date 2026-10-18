// GameType.kt — перелік ігор застосунку (PLAN §2) з стабільними route-ідентифікаторами.
package dev.gurtom.data.model

/**
 * Тип гри; [routeKey] — сталий рядок для навігаційних аргументів і аналітики,
 * не локалізується. Порядок = порядок у домі Home.
 */
enum class GameType(val routeKey: String) {
    Alias("alias"),
    Crocodile("crocodile"),
    WhoAmI("who_am_i"),
    Taboo("taboo"),
    Hat("hat"),
    WordChain("word_chain"),
    TruthOrDare("truth_or_dare"),
    NeverHaveIEver("never_have_i_ever"),
    MostLikelyTo("most_likely_to"),
    EmojiGuess("emoji_guess"),
}
