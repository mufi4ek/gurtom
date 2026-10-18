// buildSrc — збирає precompiled script plugin "gurtom.android.library"
// (спільні налаштування Android-модулів) та helper GurtomVersions.
// Плагіни застосовані до самого :buildSrc, щоб їх DSL-класи були на classpath
// компіляції precompiled scripts; версії синхронізовані з libs.versions.toml.
plugins {
    id("com.android.library") version "8.13.0"
    // kotlin-android підключається транзитивно через AGP не гарантовано —
    // тому явно, але БЕЗ конфлікту завдань: generatePgpKeys вимкнено нижче.
    id("org.jetbrains.kotlin.android") version "2.2.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.2.21" apply false
}

android {
    namespace = "ua.mufidev.gurtom.buildsrc"
    compileSdk = 35
    defaultConfig { minSdk = 24 }
}

dependencies {
    // DSL-класи Kotlin/Compose плагінів для компіляції .kts; під час
    // застосування конвенції вони вже на classpath root-проєкту.
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.compose.gradlePlugin)
}

// Конвенційний precompiled script не повинен спадкувати android-блок :buildSrc:
// усі модулі виставляють SDK самі (compileSdk 35 / minSdk 24).
tasks.matching { it.name == "extractProguardFiles" }.configureEach { enabled = false }
