# app/proguard-rules.pro — правила R8 для релізної збірки Ґуртом.
# Room, Hilt і kotlinx.serialization генерують код через reflection-friendly шляхи,
# але JSON-парсинг даних словника використовує серіалізатори — зберігаємо їхні метадані.

-dontwarn org.jetbrains.annotations.**

# kotlinx.serialization: зберігаємо companion serializers та @Serializable класи
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keepclassmembers class kotlinx.serialization.json.** {
    *** Companion;
}
-keepclasseswithmembers class kotlinx.serialization.json.** {
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class dev.gurtom.**$$serializer { *; }
-keepclassmembers class dev.gurtom.** {
    *** Companion;
}
-keepclasseswithmembers class dev.gurtom.** {
    kotlinx.serialization.KSerializer serializer(...);
}
