package ru.iandreyshev

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class YandexAgentClient(
    private val folderId: String,
    private val apiKey: String,
    private val agentId: String
) {
    private val http = OkHttpClient()
    private val mapper: ObjectMapper = ObjectMapper().registerKotlinModule()

    fun reviewCode(diff: String, changedFiles: List<String>): String {
        val prompt = buildReviewPrompt(diff, changedFiles)

        val bodyJson = JSONObject()
            .put("project", folderId)
            .put("prompt", JSONObject().put("id", agentId))
            .put("input", prompt)

        val req = Request.Builder()
            .url("https://rest-assistant.api.cloud.yandex.net/v1/responses")
            .post(bodyJson.toString().toRequestBody("application/json".toMediaType()))
            .header("Authorization", "Api-Key $apiKey")
            .header("Content-Type", "application/json")
            .build()

        http.newCall(req).execute().use { resp ->
            val body = resp.body?.string().orEmpty()

            if (!resp.isSuccessful) {
                return "Ошибка при обращении к API:\n" +
                       "HTTP код: ${resp.code}\n" +
                       "Ответ: $body"
            }

            return try {
                val node = mapper.readTree(body)

                // Проверяем статус
                val status = node["status"]?.asText()
                if (status == "failed") {
                    val errorCode = node["error"]?.get("code")?.asText() ?: "unknown"
                    val errorMsg = node["error"]?.get("message")?.asText() ?: "unknown error"
                    return "Ошибка от агента:\n" +
                           "Код: $errorCode\n" +
                           "Сообщение: $errorMsg\n\n" +
                           "Возможные причины:\n" +
                           "- Слишком большой diff\n" +
                           "- Проблема с конфигурацией агента\n" +
                           "- Временная проблема Yandex Cloud"
                }

                // Извлекаем текст из output
                node["output"]?.get(0)?.get("content")?.get(0)?.get("text")?.asText()
                    ?: "Агент не вернул текстовый ответ. Статус: $status"

            } catch (e: Exception) {
                "Ошибка при парсинге ответа:\n${e.message}\n\nСырой ответ:\n$body"
            }
        }
    }

    private fun buildReviewPrompt(diff: String, changedFiles: List<String>): String {
        return """
            Проведи code review для следующих изменений:

            Измененные файлы:
            ${changedFiles.joinToString("\n") { "- $it" }}

            Diff:
            ```
            $diff
            ```

            Проверь:
            1. Наличие потенциальных багов
            2. Качество кода и читаемость
            3. Соответствие best practices
            4. Безопасность
            5. Производительность

            Дай конкретные рекомендации по улучшению.
        """.trimIndent()
    }

    fun close() {
        // OkHttpClient не требует явного закрытия
    }
}
