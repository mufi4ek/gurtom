// feature/setup/build.gradle.kts — :feature:setup: екранний модуль (залежності лише вниз: data -> core).
plugins {
    id("gurtom.android.library")
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

android {
    namespace = "dev.gurtom.feature.setup"
}

dependencies {
    implementation(project(":core:designsystem"))
    implementation(project(":data"))
    implementation(platform(libs.compose.bom))
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.hilt.navigation.compose)
}
