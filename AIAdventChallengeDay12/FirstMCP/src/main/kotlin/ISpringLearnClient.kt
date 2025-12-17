package ru.iandreyshev

import java.net.URI
import java.net.URLEncoder
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.charset.StandardCharsets
import java.time.Instant

/**
 * Минимальный клиент для iSpring Learn REST API:
 * - Получает access token через POST /api/v3/token (client_credentials)
 * - Кэширует токен
 * - Проксирует GET /user и GET /user/{user_id}
 *
 * Настройки берутся из ENV:
 *  ISPRING_API_HOST (например https://api-learn.ispringlearn.com)
 *  ISPRING_CLIENT_ID
 *  ISPRING_CLIENT_SECRET
 */
class ISpringLearnClient(
    private val apiHost: String,
    private val clientId: String,
    private val clientSecret: String,
) {
    private val http = HttpClient.newBuilder().build()

    @Volatile private var cachedToken: String? = null
    @Volatile private var tokenExpiresAtEpochSec: Long = 0

    fun getUsers(
        departmentsCsv: String?,
        groupsCsv: String?,
        accept: String = "application/json",
    ): String {
        val query = buildQuery(
            "departments[]" to splitCsv(departmentsCsv),
            "groups[]" to splitCsv(groupsCsv),
        )

        val path = if (query.isBlank()) "/api/v2/users" else "/api/v2/users?$query"
        return get(path = path, accept = accept)
    }

    fun getUserInfo(
        userId: String,
        accept: String = "application/json",
    ): String {
        val safeId = urlEncodePathSegment(userId)
        return get(path = "/api/v2/user/$safeId", accept = accept)
    }

    private fun get(path: String, accept: String): String {
        val token = getOrRefreshToken()

        val req = HttpRequest.newBuilder()
            .uri(URI.create(apiHost.trimEnd('/') + path))
            .header("Accept", accept)
            .header("Authorization", "Bearer $token")
            .GET()
            .build()

        val resp = http.send(req, HttpResponse.BodyHandlers.ofString())

        // Возвращаем "как есть", но добавим статус строкой, чтобы было понятно что пришло.
        val contentType = resp.headers().firstValue("content-type").orElse("unknown")
        return buildString {
            appendLine("HTTP ${resp.statusCode()} ($contentType)")
            appendLine(resp.body())
        }
    }

    private fun getOrRefreshToken(): String {
        val now = Instant.now().epochSecond
        val token = cachedToken
        if (token != null && now < tokenExpiresAtEpochSec) return token

        synchronized(this) {
            val now2 = Instant.now().epochSecond
            val token2 = cachedToken
            if (token2 != null && now2 < tokenExpiresAtEpochSec) return token2

            val newToken = requestToken()
            // TTL у токена 1800 сек (30 минут). :contentReference[oaicite:7]{index=7}
            // Держим запас (25 минут), чтобы не словить истечение ровно на запросе.
            cachedToken = newToken
            tokenExpiresAtEpochSec = Instant.now().epochSecond + 25 * 60
            return newToken
        }
    }

    private fun requestToken(): String {
        // POST /api/v3/token, x-www-form-urlencoded :contentReference[oaicite:8]{index=8}
        val form = formUrlEncode(
            "client_id" to clientId,
            "client_secret" to clientSecret,
            "grant_type" to "client_credentials"
        )

        val req = HttpRequest.newBuilder()
            .uri(URI.create(apiHost.trimEnd('/') + "/api/v3/token"))
            .header("Content-Type", "application/x-www-form-urlencoded")
            .header("Accept", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(form))
            .build()

        val resp = http.send(req, HttpResponse.BodyHandlers.ofString())
        if (resp.statusCode() !in 200..299) {
            throw IllegalStateException("Failed to get token: HTTP ${resp.statusCode()} body=${resp.body()}")
        }

        // Парсим JSON без зависимостей: ищем "access_token":"..."
        val body = resp.body()
        val token = extractJsonString(body, "access_token")
            ?: throw IllegalStateException("Token response has no access_token. Body=$body")

        return token
    }
}

private fun splitCsv(csv: String?): List<String> =
    csv?.split(",")
        ?.map { it.trim() }
        ?.filter { it.isNotBlank() }
        ?: emptyList()

private fun buildQuery(vararg params: Pair<String, List<String>>): String {
    val parts = mutableListOf<String>()
    for ((key, values) in params) {
        for (v in values) {
            parts += "${urlEncode(key)}=${urlEncode(v)}"
        }
    }
    return parts.joinToString("&")
}

private fun urlEncode(s: String): String =
    URLEncoder.encode(s, StandardCharsets.UTF_8)

private fun urlEncodePathSegment(s: String): String =
    // UUID обычно безопасен, но на всякий случай:
    URLEncoder.encode(s, StandardCharsets.UTF_8).replace("+", "%20")

private fun formUrlEncode(vararg kv: Pair<String, String>): String =
    kv.joinToString("&") { (k, v) -> "${urlEncode(k)}=${urlEncode(v)}" }

private fun extractJsonString(json: String, key: String): String? {
    // Очень простой парсер под ответ вида:
    // {"access_token":"...","expires_in":1800,"token_type":"bearer"}
    val pattern = Regex(""""$key"\s*:\s*"([^"]+)"""")
    return pattern.find(json)?.groupValues?.getOrNull(1)
}
