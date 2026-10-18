// core/database/build.gradle.kts — :core:database: розпакування gurtom.db.gz, відкриття БД, Room DAO.
plugins {
    id("gurtom.android.library")
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

android {
    namespace = "dev.gurtom.core.database"
}

dependencies {
    api(project(":core:common"))
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    implementation(libs.androidx.room.paging)
    ksp(libs.androidx.room.compiler)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
}
