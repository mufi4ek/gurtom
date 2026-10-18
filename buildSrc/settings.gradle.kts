// buildSrc/settings.gradle.kts — isolated build для конвенційних плагінів;
// каталог версій доступний через from(files(...)), репозиторії оголошені тут.
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
