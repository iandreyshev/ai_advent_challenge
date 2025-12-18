package ru.iandreyshev
import com.fasterxml.jackson.core.JsonFactory
import com.fasterxml.jackson.core.json.JsonReadFeature
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.KotlinModule

object YandexOutputTextParser {

    private val mapper: ObjectMapper = ObjectMapper(
        JsonFactory.builder()
            // Важно: НЕ включаем STRICT_DUPLICATE_DETECTION — иначе упадёт на дубликатах ключей
            // На всякий случай можно разрешить некоторые "грязные" JSON-особенности:
            .enable(JsonReadFeature.ALLOW_TRAILING_COMMA)
            .enable(JsonReadFeature.ALLOW_UNESCAPED_CONTROL_CHARS)
            .build()
    ).registerModule(KotlinModule.Builder().build())

    /**
     * Возвращает все найденные output_text.text (их может быть несколько).
     */
    fun extractAllOutputTexts(json: String): List<String> {
        val root = mapper.readTree(json)

        val outputArr = root.path("output")
        if (!outputArr.isArray) return emptyList()

        val result = mutableListOf<String>()

        for (item in outputArr) {
            // ищем сообщения ассистента
            if (item.path("type").asText() != "message") continue

            val contentArr = item.path("content")
            if (!contentArr.isArray) continue

            for (content in contentArr) {
                if (content.path("type").asText() == "output_text") {
                    val text = content.path("text").asText(null)
                    if (!text.isNullOrBlank()) result += text
                }
            }
        }

        return result
    }

    /**
     * Удобный хелпер: вернуть первый output_text, либо null.
     */
    fun extractFirstOutputText(json: String): String? =
        extractAllOutputTexts(json).firstOrNull()
}
