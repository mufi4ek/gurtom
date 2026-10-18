// WordDatabaseAssetUnpacker.kt — ідемпотентне розпакування assets/gurtom.db.gz у filesDir (DATA_SCHEMA §1).
package dev.gurtom.core.database.unpack

import android.content.Context
import dev.gurtom.core.common.IoDispatcher
import java.io.File
import java.util.zip.GZIPInputStream
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext

/**
 * Розпаковує словник `gurtom.db.gz` у `context.filesDir/gurtom.db`.
 * Ідемпотентно: якщо файл уже є і версія даних збігається — нічого не робить.
 * Обов'язково викликається на IO-диспетчері; сплеш прикриває 150–300 мс роботи.
 */
@Singleton
class WordDatabaseAssetUnpacker @Inject constructor(
    private val context: Context,
    @IoDispatcher private val io: CoroutineDispatcher,
) {

    private val target: File get() = File(context.filesDir, DB_FILE_NAME)
    private val versionMarker: File get() = File(context.filesDir, VERSION_MARKER_NAME)

    /** Повертає розпакований файл БД; кидає IOException, якщо асет пошкоджено. */
    suspend fun ensureUnpacked(): File = withContext(io) {
        if (target.exists() && readInstalledVersion() == BUILD_DATA_VERSION) {
            return@withContext target
        }
        val tmp = File(context.filesDir, "$DB_FILE_NAME.tmp")
        context.assets.open(ASSET_NAME).use { input ->
            GZIPInputStream(input).use { gzip ->
                tmp.outputStream().use { out -> gzip.copyTo(out, DEFAULT_BUFFER_SIZE * 8) }
            }
        }
        if (!tmp.renameTo(target)) {
            tmp.delete()
            error("Не вдалося активувати базу даних")
        }
        writeInstalledVersion(BUILD_DATA_VERSION)
        target
    }

    private fun readInstalledVersion(): Int? =
        versionMarker.takeIf { it.exists() }?.readText()?.trim()?.toIntOrNull()

    private fun writeInstalledVersion(version: Int) {
        versionMarker.writeText(version.toString())
    }

    companion object {
        const val ASSET_NAME = "gurtom.db.gz"
        const val DB_FILE_NAME = "gurtom.db"
        private const val VERSION_MARKER_NAME = ".gurtom-data-version"

        /** Версія датасету, зібраного з цим білдом (DATA_SCHEMA §9). */
        const val BUILD_DATA_VERSION = 1
    }
}
