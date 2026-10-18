// buildSrc/build.gradle.kts — збирає конвенційні Gradle-плагіни Гуртом
// (клас AndroidLibraryConventionPlugin + реєстрація id "gurtom.android.library").
// Це ЧИСТИЙ JVM-проєкт: жодних android-плагінів тут, інакше AGP конфліктує з
// java-плагіном buildSrc ("The 'java' plugin has been applied, but it is not
// compatible with the Android plugins"). AGP/Kotlin/Compose додаються як
// implementation — тоді їх класи доступні і для компіляції, і в runtime.
plugins {
    `kotlin-dsl`
}

repositories {
    google()
    mavenCentral()
    gradlePluginPortal()
}

dependencies {
    // AGP 8.13.0 / Kotlin 2.2.21 — ті ж версії, що у gradle/libs.versions.toml.
    implementation("com.android.tools.build:gradle:8.13.0")
    implementation("org.jetbrains.kotlin:kotlin-gradle-plugin:2.2.21")
    implementation("org.jetbrains.kotlin:compose-compiler-gradle-plugin:2.2.21")
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}
