// core/designsystem/build.gradle.kts — :core:designsystem: тема Material 3, кольори, типографіка, компоненти.
plugins {
    id("gurtom.android.library")
}

android {
    namespace = "dev.gurtom.core.designsystem"
}

dependencies {
    api(platform(libs.compose.bom))
    api(libs.compose.material3)
    api(libs.compose.material.icons)
}
