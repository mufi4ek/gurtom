// build.gradle.kts — кореневий скрипт: плагіни AGP/Kotlin уже на класовому шляху
// збірки через :buildSrc (implementation-залежності), тому тут вони оголошені БЕЗ
// версій (apply false) — інакше Gradle видає "plugin is already on the classpath
// with an unknown version". KSP/Hilt/serialization застосовуються у модулях.
plugins {
    id("com.android.application") apply false
    id("com.android.library") apply false
    id("org.jetbrains.kotlin.android") apply false
    id("org.jetbrains.kotlin.plugin.compose") apply false
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.ksp) apply false
    alias(libs.plugins.hilt) apply false
}
