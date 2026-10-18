// AndroidLibraryConventionPlugin — конвенційний Gradle-плагін бібліотечного
// Android-модуля Гуртом: compileSdk 35, minSdk 24, JVM target 17, Jetpack
// Compose + Material 3 із BOM. Застосовується в модулях як
// `plugins { id("gurtom.android.library") }`.
package ua.mufidev.gurtom.convention

import com.android.build.gradle.LibraryExtension
import org.gradle.api.JavaVersion
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension

class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        // Плагіни застосовуються імперативно: AGP/Kotlin вже на classpath збірки
        // (оголошені в root build.gradle.kts через alias(... ) apply false), тому
        // версії тут не вказуємо і buildSrc залишається чистим JVM-проєктом.
        pluginManager.apply("com.android.library")
        pluginManager.apply("org.jetbrains.kotlin.android")
        pluginManager.apply("org.jetbrains.kotlin.plugin.compose")

        val libs = extensions.getByType(VersionCatalogsExtension::class).named("libs")

        extensions.configure<LibraryExtension> {
            compileSdk = 36
            defaultConfig.minSdk = 24
            // Юніт-тести на JVM: Compose/android-заглушки повертають null замість падіння.
            testOptions.unitTests.isReturnDefaultValues = true
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
            val bom = libs.findLibrary("compose-bom").get().get()
            add("implementation", platform(bom))
            add("implementation", libs.findLibrary("androidx-core-ktx").get())
            add("implementation", libs.findLibrary("compose-ui").get())
            add("implementation", libs.findLibrary("compose-ui-graphics").get())
            add("implementation", libs.findLibrary("compose-ui-tooling-preview").get())
            add("implementation", libs.findLibrary("compose-material3").get())
            add("debugImplementation", libs.findLibrary("compose-ui-tooling").get())
        }
    }
}
