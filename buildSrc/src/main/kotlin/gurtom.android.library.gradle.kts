// gurtom.android.library.gradle.kts — конвенції бібліотечного Android-модуля Ґуртом:
// compileSdk 35, minSdk 24, JVM target 17, Jetpack Compose + Material 3 із BOM.
import com.android.build.gradle.BaseExtension
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension

plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

extensions.configure<BaseExtension> {
    compileSdkVersion(35)
    defaultConfig {
        minSdk = 24
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

extensions.configure<KotlinAndroidProjectExtension> {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

dependencies {
    "implementation"(platform(libs.compose.bom))
    "implementation"(libs.androidx.core.ktx)
    "implementation"(libs.compose.ui)
    "implementation"(libs.compose.ui.graphics)
    "implementation"(libs.compose.ui.tooling.preview)
    "implementation"(libs.compose.material3)
    "debugImplementation"(libs.compose.ui.tooling)
}
