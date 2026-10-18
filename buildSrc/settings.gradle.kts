// buildSrc/settings.gradle.kts — isolated build конвенційних плагінів.
// Каталог версій libs підключається з ../gradle/libs.versions.toml, щоб
// клас плагіна міг читати версії через VersionCatalogsExtension у споживачів.
dependencyResolutionManagement {
    versionCatalogs {
        create("libs") {
            from(files("../gradle/libs.versions.toml"))
        }
    }
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

rootProject.name = "GurtomBuildSrc"
