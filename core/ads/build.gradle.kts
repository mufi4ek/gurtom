// core/ads/build.gradle.kts — :core:ads: AdManager і AdPolicy (поки заглушки-інтерфейси).
plugins {
    id("gurtom.android.library")
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

android {
    namespace = "dev.gurtom.core.ads"
}

dependencies {
    api(project(":core:common"))
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
}
