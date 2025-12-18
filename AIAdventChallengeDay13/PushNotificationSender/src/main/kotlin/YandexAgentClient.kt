package ru.iandreyshev

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

object YandexAgentClient {

    private const val URL =
        "https://rest-assistant.api.cloud.yandex.net/v1/responses"

    private val PROMPT = """
       Составь короткое саммари на 1-2 предложения в юморном стиле о том какие напоминания у меня записаны
    """.trimIndent()

    fun getSummary(): String {
        val apiKey = System.getenv("YANDEX_API_KEY")
            ?: error("YANDEX_API_KEY not set")
        val folderId = System.getenv("YANDEX_FOLDER_ID")
            ?: error("YANDEX_FOLDER_ID not set")
        val promptId = System.getenv("YANDEX_PROMPT_ID")
            ?: error("YANDEX_PROMPT_ID not set")

        val client = OkHttpClient()

        val bodyJson = JSONObject()
            .put("project", folderId)
            .put(
                "prompt",
                JSONObject().put("id", promptId)
            )
            .put("input", PROMPT)

        val request = Request.Builder()
            .url(URL)
            .post(
                bodyJson.toString()
                    .toRequestBody("application/json".toMediaType())
            )
            .addHeader("Authorization", "Api-Key $apiKey")
            .addHeader("Content-Type", "application/json")
            .build()

        client.newCall(request).execute().use { response ->
            val raw = response.body?.string()
                ?: error("Empty response from Yandex")

            if (!response.isSuccessful) {
                error("Yandex error ${response.code}: $raw")
            }

            return YandexOutputTextParser.extractFirstOutputText(raw).orEmpty()
        }
    }
}
