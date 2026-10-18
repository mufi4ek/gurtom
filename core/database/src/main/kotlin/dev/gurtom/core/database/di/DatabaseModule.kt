// DatabaseModule.kt — Hilt-доступ до Room поверх розпакованого filesDir/gurtom.db (DATA_SCHEMA §1).
package dev.gurtom.core.database.di

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import dev.gurtom.core.database.dao.PartyDao
import dev.gurtom.core.database.dao.PartyEntity
import dev.gurtom.core.database.dao.WordEntity
import dev.gurtom.core.database.dao.WordsDao
import dev.gurtom.core.database.unpack.WordDatabaseAssetUnpacker
import java.io.File
import javax.inject.Singleton

/**
 * Обгортка над словником: БД розпаковує [WordDatabaseAssetUnpacker], Room відкриває готовий файл.
 * schemaVersion = BUILD_DATA_VERSION датасету, тож міграції не потрібні —
 * оновлення контенту іде разом з новою версією ассета.
 */
@Database(
    entities = [WordEntity::class, PartyEntity::class],
    version = WordDatabaseAssetUnpacker.BUILD_DATA_VERSION,
    exportSchema = false,
)
abstract class GurtomDatabase : RoomDatabase() {

    abstract fun wordsDao(): WordsDao

    abstract fun partyDao(): PartyDao
}

/** Hilt-модуль доступу до бази словника та вечірніх карток. */
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): GurtomDatabase =
        // Шлях згідно з DATA_SCHEMA §1: filesDir/gurtom.db, а не стандартний databases/.
        Room.databaseBuilder(
            context,
            GurtomDatabase::class.java,
            File(context.filesDir, WordDatabaseAssetUnpacker.DB_FILE_NAME),
        ).build()

    @Provides
    fun provideWordsDao(db: GurtomDatabase): WordsDao = db.wordsDao()

    @Provides
    fun providePartyDao(db: GurtomDatabase): PartyDao = db.partyDao()
}
