// buildSrc — збирає precompiled script plugin "gurtom.android.library"
// (спільні налаштування Android-модулів). Класи плагінів доступні для
// компіляції скрипта через implementation-залежності; версії — з каталогу.
plugins {
    `kotlin-dsl`
}

dependencies {
    // Плагіни застосовуються без версії: її гарантує root build classpath
    // (кореневий build.gradle.kts оголошує AGP/Kotlin/Compose з каталогу).
    // compileOnly — щоб не конфліктувало з already-on-classpath у root.
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.compose.gradlePlugin)
}
