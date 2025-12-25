package ru.iandreyshev.ai

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import ru.iandreyshev.RankedPick
import ru.iandreyshev.ScoredCandidate

class YandexLlmClient(
    private val folderId: String,
    private val apiKey: String,
    private val agentId: String
) : LlmClient {

    private val http = OkHttpClient()
    private val mapper: ObjectMapper = ObjectMapper().registerKotlinModule()

    override fun rewriteQueries(question: String): List<String> {
        return emptyList()
        val prompt = """
Ты — помощник по поиску по чату (RAG). Переформулируй вопрос 3 разными способами, сохранив смысл.
Важно: не добавляй новых фактов и не меняй критерии.

Вопрос:
$question

Верни СТРОГО JSON:
{
  "queries": ["...", "...", "..."]
}
        """.trimIndent()

        val text = call(prompt)
        val json = extractJson(text)
        val node = mapper.readTree(json)
        val arr = node["queries"] ?: error("No 'queries' field")
        val list = arr.map { it.asText() }.map { it.trim() }.filter { it.isNotBlank() }

        // Требуем ровно 3, но если LLM ошибся — нормализуем максимально безопасно
        return when {
            list.size >= 3 -> list.take(3)
            list.isEmpty() -> listOf(question, question, question).take(3)
            else -> (list + List(3 - list.size) { list.last() }).take(3)
        }
    }

    override fun rankChunks(
        queries: List<String>,
        candidates: List<ScoredCandidate>,
        finalTopN: Int
    ): List<RankedPick> {
        val candidatesBlock = buildString {
            for (c in candidates) {
                append("chunkId=").append(c.chunk.chunkId)
                    .append(" fusion=").append("%.6f".format(c.fusionScore))
                    .append(" bestCos=").append("%.4f".format(c.bestScore))
                    .append("\n")
                append(c.chunk.text.take(800).replace("\n", " "))
                append("\n\n")
            }
        }

        val prompt = """
Ты выбираешь лучшие фрагменты чата для ответа на один из вопросов и ДОЛЖЕН дать доказательство (цитату).

Вопросы:
$queries

Кандидаты:
$candidatesBlock

Выбери до $finalTopN кандидатов (можно меньше, если нет доказательств).
Верни СТРОГО JSON:
{
  "best": [
    {"chunkId": "chunkId1", "evidence": "точная цитата..."},
    {"chunkId": "chunkId2", "evidence": "точная цитата..."}
  ]
}
        """.trimIndent()

        val text = call(prompt)
        val json = extractJson(text)
        val node = mapper.readTree(json)

        val arr = node["best"] ?: error("No 'best' field")

        return arr.mapNotNull { item ->
            val id = item["chunkId"]?.asText()?.trim().orEmpty()
            val ev = item["evidence"]?.asText()?.trim().orEmpty()
            if (id.isBlank() || ev.isBlank()) return@mapNotNull null
            if (candidates.none { it.chunk.chunkId == id }) return@mapNotNull null
            RankedPick(chunkId = id, evidence = ev)
        }.take(finalTopN)
    }

    private fun call(prompt: String): String {
        val bodyJson = JSONObject()
            .put("project", folderId)
            .put(
                "prompt",
                JSONObject().put("id", agentId)
            )
            .put("input", prompt)

        val req = Request.Builder()
            .url("https://rest-assistant.api.cloud.yandex.net/v1/responses")
            .post(
                bodyJson.toString()
                    .toRequestBody("application/json".toMediaType())
            )
            .header("Authorization", "Api-Key $apiKey")
            .header("Content-Type", "application/json")
            .build()

        http.newCall(req).execute().use { resp ->
            val body = resp.body?.string().orEmpty()
            if (!resp.isSuccessful) {
                error("YandexGPT failed: HTTP ${resp.code} $body")
            }
            val node = mapper.readTree(body)
            return node["output"][0]["content"][0]["text"].asText()
        }
    }

    // ---------- helpers ----------

    private fun extractJson(text: String): String {
        val start = text.indexOf('{')
        val end = text.lastIndexOf('}')

        require(start in 0..<end) { "No JSON found in response:\n$text" }

        return text.substring(start, end + 1)
    }
}
