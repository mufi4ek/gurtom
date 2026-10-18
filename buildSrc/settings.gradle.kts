// buildSrc/settings.gradle.kts — isolated build для конвенційних плагінів;
// каталог версій доступний через from(files(...)), репозиторії оголошені тут.
// pluginManagement теж обов'язковий: без нього plugins DSL у buildSrc
// шукає маркер com.android.library лише на Gradle Plugin Portal (404).
pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    versionCatalogs {
        create("libs") {
            from(files("../gradle/libs.versions.toml"))
        }
    }
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "GurtomBuildSrc"
