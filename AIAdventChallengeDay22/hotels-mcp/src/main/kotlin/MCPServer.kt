package ru.iandreyshev

import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.types.*
import kotlinx.serialization.json.*
import java.io.BufferedReader
import java.io.InputStreamReader

data class User(
    val id: String,
    val email: String,
    val name: String,
    val registeredAt: String,
    val plan: String,
    val status: String
)

data class Ticket(
    val id: String,
    val userId: String,
    val subject: String,
    val description: String,
    val status: String,
    val priority: String,
    val category: String,
    val createdAt: String,
    val updatedAt: String,
    val tags: List<String>,
    val resolution: String? = null
)

data class SupportData(
    val users: List<User>,
    val tickets: List<Ticket>
)

fun buildMcpServer(): Server {
    val supportData = loadSupportDataFromJson("/support.json")

    val server = Server(
        serverInfo = Implementation(
            name = "support-mcp",
            version = "1.0.0",
            title = "TaskFlow Support MCP Server"
        ),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    // Tool: get_user_info
    // args:
    //   userId: string (required) - ID или email пользователя
    server.addTool(
        name = "get_user_info",
        description = "Получить информацию о пользователе TaskFlow по ID или email"
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val userIdOrEmail = argString(args, "userId").orEmpty()

        if (userIdOrEmail.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"userId is required"}"""))
            )
        }

        val user = supportData.users.firstOrNull {
            it.id.equals(userIdOrEmail, ignoreCase = true) ||
                    it.email.equals(userIdOrEmail, ignoreCase = true)
        } ?: return@addTool CallToolResult(
            content = listOf(TextContent("""{"error":"user not found","userId":"${escapeJson(userIdOrEmail)}"}"""))
        )

        val json = """{
          "id":"${escapeJson(user.id)}",
          "email":"${escapeJson(user.email)}",
          "name":"${escapeJson(user.name)}",
          "registeredAt":"${escapeJson(user.registeredAt)}",
          "plan":"${escapeJson(user.plan)}",
          "status":"${escapeJson(user.status)}"
        }""".trimIndent()

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: get_ticket
    // args:
    //   ticketId: string (required)
    server.addTool(
        name = "get_ticket",
        description = "Получить подробную информацию о тикете поддержки по ID"
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val ticketId = argString(args, "ticketId").orEmpty()

        if (ticketId.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"ticketId is required"}"""))
            )
        }

        val ticket = supportData.tickets.firstOrNull {
            it.id.equals(ticketId, ignoreCase = true)
        } ?: return@addTool CallToolResult(
            content = listOf(TextContent("""{"error":"ticket not found","ticketId":"${escapeJson(ticketId)}"}"""))
        )

        val user = supportData.users.firstOrNull { it.id == ticket.userId }

        val json = """{
          "id":"${escapeJson(ticket.id)}",
          "userId":"${escapeJson(ticket.userId)}",
          "userEmail":"${escapeJson(user?.email ?: "unknown")}",
          "userName":"${escapeJson(user?.name ?: "unknown")}",
          "userPlan":"${escapeJson(user?.plan ?: "unknown")}",
          "subject":"${escapeJson(ticket.subject)}",
          "description":"${escapeJson(ticket.description)}",
          "status":"${escapeJson(ticket.status)}",
          "priority":"${escapeJson(ticket.priority)}",
          "category":"${escapeJson(ticket.category)}",
          "createdAt":"${escapeJson(ticket.createdAt)}",
          "updatedAt":"${escapeJson(ticket.updatedAt)}",
          "tags":[${ticket.tags.joinToString(",") { """"${escapeJson(it)}"""" }}],
          "resolution":${if (ticket.resolution != null) """"${escapeJson(ticket.resolution)}"""" else "null"}
        }""".trimIndent()

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: search_tickets
    // args:
    //   userId: string (optional) - фильтр по ID пользователя
    //   status: string (optional) - open, in_progress, resolved
    //   category: string (optional) - authentication, tasks, notifications, sync, billing, account, integrations
    //   priority: string (optional) - low, medium, high
    server.addTool(
        name = "search_tickets",
        description = "Поиск тикетов поддержки по различным фильтрам (userId, status, category, priority)"
    ) { request ->
        val args = request.arguments ?: emptyMap()

        val userId = argString(args, "userId")
        val status = argString(args, "status")
        val category = argString(args, "category")
        val priority = argString(args, "priority")

        val filtered = supportData.tickets.asSequence()
            .filter { userId == null || it.userId.equals(userId, ignoreCase = true) }
            .filter { status == null || it.status.equals(status, ignoreCase = true) }
            .filter { category == null || it.category.equals(category, ignoreCase = true) }
            .filter { priority == null || it.priority.equals(priority, ignoreCase = true) }
            .sortedWith(
                compareByDescending<Ticket> { it.priority == "high" }
                    .thenByDescending { it.updatedAt }
            )
            .toList()

        val json = buildJsonArray(filtered.map { t ->
            val user = supportData.users.firstOrNull { it.id == t.userId }
            """{
              "id":"${escapeJson(t.id)}",
              "userId":"${escapeJson(t.userId)}",
              "userEmail":"${escapeJson(user?.email ?: "unknown")}",
              "userName":"${escapeJson(user?.name ?: "unknown")}",
              "subject":"${escapeJson(t.subject)}",
              "status":"${escapeJson(t.status)}",
              "priority":"${escapeJson(t.priority)}",
              "category":"${escapeJson(t.category)}",
              "createdAt":"${escapeJson(t.createdAt)}",
              "updatedAt":"${escapeJson(t.updatedAt)}"
            }""".trimIndent()
        })

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: get_user_tickets
    // args:
    //   userId: string (required) - ID пользователя
    server.addTool(
        name = "get_user_tickets",
        description = "Получить все тикеты конкретного пользователя"
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val userId = argString(args, "userId").orEmpty()

        if (userId.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"userId is required"}"""))
            )
        }

        val user = supportData.users.firstOrNull {
            it.id.equals(userId, ignoreCase = true) ||
                    it.email.equals(userId, ignoreCase = true)
        }

        if (user == null) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"user not found","userId":"${escapeJson(userId)}"}"""))
            )
        }

        val userTickets = supportData.tickets
            .filter { it.userId == user.id }
            .sortedByDescending { it.updatedAt }

        val json = buildJsonArray(userTickets.map { t ->
            """{
              "id":"${escapeJson(t.id)}",
              "subject":"${escapeJson(t.subject)}",
              "description":"${escapeJson(t.description)}",
              "status":"${escapeJson(t.status)}",
              "priority":"${escapeJson(t.priority)}",
              "category":"${escapeJson(t.category)}",
              "createdAt":"${escapeJson(t.createdAt)}",
              "updatedAt":"${escapeJson(t.updatedAt)}",
              "tags":[${t.tags.joinToString(",") { """"${escapeJson(it)}"""" }}]
            }""".trimIndent()
        })

        CallToolResult(content = listOf(TextContent(json)))
    }

    return server
}

fun loadSupportDataFromJson(resourcePath: String): SupportData {
    val stream = object {}.javaClass.getResourceAsStream(resourcePath)
        ?: throw IllegalStateException("Resource not found: $resourcePath (put it in src/main/resources)")

    val jsonText = BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).use { it.readText() }
    val jsonElement = Json.parseToJsonElement(jsonText).jsonObject

    val users = jsonElement["users"]?.jsonArray?.map { userElement ->
        val obj = userElement.jsonObject
        User(
            id = obj["id"]?.jsonPrimitive?.content ?: "",
            email = obj["email"]?.jsonPrimitive?.content ?: "",
            name = obj["name"]?.jsonPrimitive?.content ?: "",
            registeredAt = obj["registeredAt"]?.jsonPrimitive?.content ?: "",
            plan = obj["plan"]?.jsonPrimitive?.content ?: "",
            status = obj["status"]?.jsonPrimitive?.content ?: ""
        )
    } ?: emptyList()

    val tickets = jsonElement["tickets"]?.jsonArray?.map { ticketElement ->
        val obj = ticketElement.jsonObject
        Ticket(
            id = obj["id"]?.jsonPrimitive?.content ?: "",
            userId = obj["userId"]?.jsonPrimitive?.content ?: "",
            subject = obj["subject"]?.jsonPrimitive?.content ?: "",
            description = obj["description"]?.jsonPrimitive?.content ?: "",
            status = obj["status"]?.jsonPrimitive?.content ?: "",
            priority = obj["priority"]?.jsonPrimitive?.content ?: "",
            category = obj["category"]?.jsonPrimitive?.content ?: "",
            createdAt = obj["createdAt"]?.jsonPrimitive?.content ?: "",
            updatedAt = obj["updatedAt"]?.jsonPrimitive?.content ?: "",
            tags = obj["tags"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList(),
            resolution = obj["resolution"]?.jsonPrimitive?.content
        )
    } ?: emptyList()

    return SupportData(users, tickets)
}

private fun buildJsonArray(items: List<String>): String =
    "[${items.joinToString(",")}]"

private fun escapeJson(s: String): String =
    s.replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")

private fun argString(args: Map<String, Any?>, key: String): String? {
    val v = args[key] ?: return null
    val s = when (v) {
        is String -> v
        is JsonPrimitive -> v.content
        else -> v.toString()
    }.trim()
    return s.removeSurrounding("\"").trim()
}
