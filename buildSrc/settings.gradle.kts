// buildSrc/settings.gradle.kts — isolated build для конвенційних плагінів;
// каталог версій доступний через from(files(...)), репозиторії оголошені тут.
// rootProject.name обов'язковий: інакше Gradle не генерує DSL-доступ до
// version catalog `libs` у precompiled script plugins (Unresolved reference: libs).
rootProject.name = "GurtomBuildSrc"

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
