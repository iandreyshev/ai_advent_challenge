package ru.iandreyshev.assistant

import io.github.oshai.kotlinlogging.KotlinLogging
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

private val logger = KotlinLogging.logger {}

class SupportAssistant(
    private val ragSystem: RAGSystem,
    private val ollamaClient: OllamaClient,
    private val mcpServerUrl: String = "http://localhost:8080",
    private val httpClient: HttpClient
) {
    private val json = Json { ignoreUnknownKeys = true }

    // MCP Tools definition
    private val mcpTools = listOf(
        ToolDefinition(
            function = FunctionDefinition(
                name = "get_user_info",
                description = "Получить информацию о пользователе TaskFlow по его ID или email",
                parameters = ToolParameters(
                    properties = mapOf(
                        "userId" to PropertyDefinition(
                            type = "string",
                            description = "ID или email пользователя"
                        )
                    ),
                    required = listOf("userId")
                )
            )
        ),
        ToolDefinition(
            function = FunctionDefinition(
                name = "get_user_tickets",
                description = "Получить все тикеты поддержки конкретного пользователя",
                parameters = ToolParameters(
                    properties = mapOf(
                        "userId" to PropertyDefinition(
                            type = "string",
                            description = "ID или email пользователя"
                        )
                    ),
                    required = listOf("userId")
                )
            )
        ),
        ToolDefinition(
            function = FunctionDefinition(
                name = "get_ticket",
                description = "Получить подробную информацию о конкретном тикете поддержки",
                parameters = ToolParameters(
                    properties = mapOf(
                        "ticketId" to PropertyDefinition(
                            type = "string",
                            description = "ID тикета"
                        )
                    ),
                    required = listOf("ticketId")
                )
            )
        )
    )

    suspend fun answerQuestion(
        question: String,
        userId: String? = null,
        ticketId: String? = null
    ): String {
        logger.info { "❓ Processing question: $question" }

        // 1. Получаем контекст из RAG (документация)
        val relevantDocs = ragSystem.retrieveRelevantDocs(question, topK = 3)
        val docsContext = relevantDocs.joinToString("\n\n") { doc ->
            "Из ${doc.metadata["source"]}:\n${doc.text}"
        }

        // 2. Получаем контекст из MCP (симуляция tool calling)
        val mcpContext = if (userId != null || ticketId != null) {
            logger.info { "🔧 Calling MCP tools for user=$userId, ticket=$ticketId" }
            buildMcpContext(userId, ticketId)
        } else {
            ""
        }

        // 3. Формируем полный промпт
        val fullPrompt = buildString {
            appendLine("Ты - ассистент технической поддержки продукта TaskFlow.")
            appendLine()
            appendLine("=== ДОКУМЕНТАЦИЯ ===")
            appendLine(docsContext)
            appendLine()
            if (mcpContext.isNotBlank()) {
                appendLine("=== ДАННЫЕ ИЗ CRM (MCP) ===")
                appendLine(mcpContext)
                appendLine()
            }
            appendLine("ВОПРОС ПОЛЬЗОВАТЕЛЯ: $question")
            appendLine()
            appendLine("Инструкции:")
            appendLine("1. Отвечай на русском языке")
            appendLine("2. Используй документацию и данные из CRM для персонализированного ответа")
            appendLine("3. Давай конкретные и понятные решения")
            appendLine("4. Если есть пошаговое решение - опиши его")
        }

        // 4. Генерируем ответ через llama3.1
        logger.info { "🤖 Using llama3.1 (with RAG + MCP context)" }
        val answer = ollamaClient.generateResponse(fullPrompt.trimIndent(), model = "llama3.1")

        logger.info { "✅ Generated answer (length: ${answer.length})" }
        return answer
    }

    private suspend fun buildMcpContext(userId: String?, ticketId: String?): String {
        val context = StringBuilder()

        try {
            if (userId != null) {
                val userInfo = callMcpEndpoint("/api/get_user_info", """{"userId":"$userId"}""")
                val userTickets = callMcpEndpoint("/api/get_user_tickets", """{"userId":"$userId"}""")

                context.appendLine("Пользователь:")
                context.appendLine(formatUserInfo(userInfo))
                context.appendLine()
                context.appendLine("История обращений:")
                context.appendLine(formatUserTickets(userTickets))
                context.appendLine()
            }

            if (ticketId != null) {
                val ticketInfo = callMcpEndpoint("/api/get_ticket", """{"ticketId":"$ticketId"}""")
                context.appendLine("Текущий тикет:")
                context.appendLine(formatTicketInfo(ticketInfo))
                context.appendLine()
            }
        } catch (e: Exception) {
            logger.error(e) { "Failed to fetch MCP context" }
        }

        return context.toString()
    }

    private fun formatUserInfo(jsonText: String): String {
        return try {
            val obj = json.parseToJsonElement(jsonText).jsonObject
            """
            - Email: ${obj["email"]?.jsonPrimitive?.content}
            - Имя: ${obj["name"]?.jsonPrimitive?.content}
            - План: ${obj["plan"]?.jsonPrimitive?.content}
            - Статус: ${obj["status"]?.jsonPrimitive?.content}
            """.trimIndent()
        } catch (e: Exception) {
            jsonText
        }
    }

    private fun formatUserTickets(jsonText: String): String {
        return try {
            val array = json.parseToJsonElement(jsonText).jsonArray
            array.joinToString("\n") { ticket ->
                val obj = ticket.jsonObject
                "- [${obj["status"]?.jsonPrimitive?.content}] ${obj["subject"]?.jsonPrimitive?.content}"
            }
        } catch (e: Exception) {
            jsonText
        }
    }

    private fun formatTicketInfo(jsonText: String): String {
        return try {
            val obj = json.parseToJsonElement(jsonText).jsonObject
            """
            - Тема: ${obj["subject"]?.jsonPrimitive?.content}
            - Статус: ${obj["status"]?.jsonPrimitive?.content}
            - Приоритет: ${obj["priority"]?.jsonPrimitive?.content}
            - Описание: ${obj["description"]?.jsonPrimitive?.content}
            """.trimIndent()
        } catch (e: Exception) {
            jsonText
        }
    }

    private suspend fun executeMcpTool(toolName: String, arguments: String): String {
        logger.info { "🔧 Executing MCP tool: $toolName with args: $arguments" }

        return try {
            when (toolName) {
                "get_user_info" -> {
                    val args = json.parseToJsonElement(arguments).jsonObject
                    val userId = args["userId"]?.jsonPrimitive?.content ?: ""
                    callMcpEndpoint("/api/get_user_info", """{"userId":"$userId"}""")
                }
                "get_user_tickets" -> {
                    val args = json.parseToJsonElement(arguments).jsonObject
                    val userId = args["userId"]?.jsonPrimitive?.content ?: ""
                    callMcpEndpoint("/api/get_user_tickets", """{"userId":"$userId"}""")
                }
                "get_ticket" -> {
                    val args = json.parseToJsonElement(arguments).jsonObject
                    val ticketId = args["ticketId"]?.jsonPrimitive?.content ?: ""
                    callMcpEndpoint("/api/get_ticket", """{"ticketId":"$ticketId"}""")
                }
                else -> """{"error": "Unknown tool: $toolName"}"""
            }
        } catch (e: Exception) {
            logger.error(e) { "Failed to execute MCP tool: $toolName" }
            """{"error": "${e.message}"}"""
        }
    }

    private suspend fun callMcpEndpoint(endpoint: String, body: String): String {
        val response: HttpResponse = httpClient.post("$mcpServerUrl$endpoint") {
            contentType(ContentType.Application.Json)
            setBody(body)
        }
        return response.bodyAsText()
    }

}
