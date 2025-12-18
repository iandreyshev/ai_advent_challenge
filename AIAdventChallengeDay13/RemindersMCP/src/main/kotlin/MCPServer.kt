package ru.iandreyshev

import com.google.auth.oauth2.GoogleCredentials
import com.google.cloud.firestore.Firestore
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.cloud.FirestoreClient
import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.types.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

private val MSK: ZoneId = ZoneId.of("Europe/Moscow")
private val ISO_FMT: DateTimeFormatter = DateTimeFormatter.ISO_OFFSET_DATE_TIME

fun buildMcpServer(): Server {
    val firestore = initFirestore()

    val server = Server(
        serverInfo = Implementation(
            name = "reminders-mcp",
            version = "1.0.0",
            title = "Reminders MCP Server (Firestore)"
        ),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    // MCP Tool: get_active_reminders
    // args (optional):
    //   limit: "50"
    server.addTool(
        name = "get_active_reminders",
        description = "Получить список активных напоминаний из Firestore (collection: reminders)"
    ) { request ->
        val limit = request.arguments?.get("limit")?.toString()?.trim()?.toIntOrNull()?.coerceIn(1, 500) ?: 50

        val bodyJson = withContext(Dispatchers.IO) {
            getActiveRemindersJson(firestore, limit)
        }

        CallToolResult(
            content = listOf(TextContent(bodyJson))
        )
    }

    return server
}

private fun initFirestore(): Firestore {
    try {
        if (FirebaseApp.getApps().isEmpty()) {
            val creds = GoogleCredentials.getApplicationDefault()
            val options = FirebaseOptions.builder()
                .setCredentials(creds)
                .build()
            FirebaseApp.initializeApp(options)
        }
        return FirestoreClient.getFirestore()
    } catch (e: Exception) {
        System.err.println("Firestore init failed: ${e::class.qualifiedName}: ${e.message}")
        e.printStackTrace()
        throw e
    }
}

private fun getActiveRemindersJson(firestore: Firestore, limit: Int): String {
    println("Getting active reminders")

    val snapshot = firestore.collection("reminders")
        .whereEqualTo("isActive", true)
        .orderBy("dueAt") // нужен composite index (тот же, что для iOS запроса)
        .limit(limit)
        .get()
        .get()

    // Возвращаем JSON строкой (агенту удобно)
    val items = snapshot.documents.mapNotNull { doc ->
        val text = doc.getString("text") ?: return@mapNotNull null
        val importance = doc.getString("importance") ?: "normal"
        val dueAtTs = doc.getTimestamp("dueAt") ?: return@mapNotNull null

        val dueAtInstant: Instant = dueAtTs.toDate().toInstant()
        val dueAtMskIso = ISO_FMT.format(dueAtInstant.atZone(MSK))

        """{
          "id":"${escapeJson(doc.id)}",
          "text":"${escapeJson(text)}",
          "dueAtMskIso":"${escapeJson(dueAtMskIso)}",
          "importance":"${escapeJson(importance)}"
        }""".trimIndent()
    }

    val result = "[${items.joinToString(",")}]"

    println(result)

    return result
}

private fun escapeJson(s: String): String =
    s.replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
