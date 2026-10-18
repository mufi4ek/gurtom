// buildSrc — збирає precompiled script plugin "gurtom.android.library"
// (спільні налаштування Android-модулів) і експортує catalog `libs` у підпроєкти.
plugins {
    `kotlin-dsl`
}

dependencies {
    implementation(libs.android.gradlePlugin)
    implementation(libs.kotlin.gradlePlugin)
    implementation(libs.compose.gradlePlugin)
}
