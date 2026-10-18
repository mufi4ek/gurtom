// gurtom.android.library.gradle.kts — конвенції бібліотечного Android-модуля Гуртом:
// compileSdk 35, minSdk 24, JVM target 17, Jetpack Compose + Material 3 із BOM.
import com.android.build.gradle.BaseExtension
import com.android.build.gradle.TestedExtension
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension

// Плагіни застосовуються без версії (класи вже на classpath buildSrc), а
// version-catalog DSL у precompiled scripts недоступний — версії беремо з
// gradle.properties (ключі gurtom.* синхронізовані з gradle/libs.versions.toml).
val agpVersion = providers.gradleProperty("gurtom.agp").get()
val kotlinVersion = providers.gradleProperty("gurtom.kotlin").get()

plugins {
    id("com.android.library") version agpVersion
    id("org.jetbrains.kotlin.android") version kotlinVersion
    id("org.jetbrains.kotlin.plugin.compose") version kotlinVersion
}

extensions.configure<BaseExtension> {
    compileSdkVersion(35)
    defaultConfig {
        minSdk = 24
    }
    // Юніт-тести на JVM: Compose-залежні класи не лоадяться під час звичайних
    // unitTest — перетворюємо UnsatisfiedLinkError/NoClassDefFound на null замість падіння.
    (this as TestedExtension).testOptions.unitTests.isReturnDefaultValues = true
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

// У precompiled script plugins DSL-доступу `libs` немає (каталог визначено в
// isolated build), тому залежності додаємо координатами з gradle.properties
// (версії синхронізовані з gradle/libs.versions.toml — там вони ж для app/features).
val bomVersion = providers.gradleProperty("gurtom.composeBom").get()
val coreKtxVersion = providers.gradleProperty("gurtom.coreKtx").get()
val composeUiVersion = providers.gradleProperty("gurtom.composeUi").get()
val material3Version = providers.gradleProperty("gurtom.material3").get()

dependencies {
    "implementation"(platform("androidx.compose:compose-bom:$bomVersion"))
    "implementation"("androidx.core:core-ktx:$coreKtxVersion")
    "implementation"("androidx.compose.ui:ui:$composeUiVersion")
    "implementation"("androidx.compose.ui:ui-graphics:$composeUiVersion")
    "implementation"("androidx.compose.ui:ui-tooling-preview:$composeUiVersion")
    "implementation"("androidx.compose.material3:material3:$material3Version")
    "debugImplementation"("androidx.compose.ui:ui-tooling:$composeUiVersion")
}
