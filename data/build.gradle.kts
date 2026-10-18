// data/build.gradle.kts — :data: репозиторії контенту та ігровий рушій (залежить лише вниз на :core).
plugins {
    id("gurtom.android.library")
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

android {
    namespace = "dev.gurtom.data"
}

dependencies {
    api(project(":core:common"))
    api(project(":core:database"))
    implementation(project(":core:ads"))
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
}
