// settings.gradle.kts — корінь багатомодульного проєкту Ґуртом.
// Усі модулі підключені через include; версії бібліотек централізовано в gradle/libs.versions.toml.
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
    repositoriesMode.set(RepositoriesMode.PREFER_SETTINGS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "gurtom"

include(":app")

include(":core:designsystem")
include(":core:database")
include(":core:common")
include(":core:ads")

include(":data")

include(":feature:home")
include(":feature:setup")
include(":feature:splash")
include(":feature:game")
include(":feature:lobby")
include(":feature:settings")
include(":feature:profile")
