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
                description = "Получить информацию о члене команды по ID или email",
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
                name = "get_user_tasks",
                description = "Получить все задачи, назначенные конкретному пользователю",
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
                name = "get_task",
                description = "Получить подробную информацию о конкретной задаче",
                parameters = ToolParameters(
                    properties = mapOf(
                        "taskId" to PropertyDefinition(
                            type = "string",
                            description = "ID задачи"
                        )
                    ),
                    required = listOf("taskId")
                )
            )
        ),
        ToolDefinition(
            function = FunctionDefinition(
                name = "search_tasks",
                description = "Поиск задач по фильтрам (projectId, assigneeId, status, priority)",
                parameters = ToolParameters(
                    properties = mapOf(
                        "projectId" to PropertyDefinition(
                            type = "string",
                            description = "ID проекта (optional)"
                        ),
                        "assigneeId" to PropertyDefinition(
                            type = "string",
                            description = "ID исполнителя (optional)"
                        ),
                        "status" to PropertyDefinition(
                            type = "string",
                            description = "Статус задачи: todo, in_progress, done, blocked (optional)"
                        ),
                        "priority" to PropertyDefinition(
                            type = "string",
                            description = "Приоритет: low, medium, high, urgent (optional)"
                        )
                    ),
                    required = emptyList()
                )
            )
        ),
        ToolDefinition(
            function = FunctionDefinition(
                name = "create_task",
                description = "Создать новую задачу в проекте",
                parameters = ToolParameters(
                    properties = mapOf(
                        "projectId" to PropertyDefinition(
                            type = "string",
                            description = "ID проекта"
                        ),
                        "title" to PropertyDefinition(
                            type = "string",
                            description = "Название задачи"
                        ),
                        "description" to PropertyDefinition(
                            type = "string",
                            description = "Описание задачи"
                        ),
                        "priority" to PropertyDefinition(
                            type = "string",
                            description = "Приоритет: low, medium, high, urgent"
                        ),
                        "assigneeId" to PropertyDefinition(
                            type = "string",
                            description = "ID исполнителя"
                        ),
                        "createdBy" to PropertyDefinition(
                            type = "string",
                            description = "ID создателя"
                        ),
                        "dueDate" to PropertyDefinition(
                            type = "string",
                            description = "Срок выполнения в формате ISO (optional)"
                        ),
                        "tags" to PropertyDefinition(
                            type = "string",
                            description = "Теги через запятую (optional)"
                        ),
                        "estimatedHours" to PropertyDefinition(
                            type = "number",
                            description = "Оценка в часах (optional)"
                        )
                    ),
                    required = listOf("projectId", "title", "description", "priority", "assigneeId", "createdBy")
                )
            )
        )
    )

    suspend fun answerQuestion(
        question: String,
        userId: String? = null,
        taskId: String? = null,
        includeRecommendations: Boolean = false,
        temperature: Double = 0.7
    ): String {
        logger.info { "❓ Processing question: $question" }

        // 1. Получаем контекст из RAG (документация)
        val relevantDocs = ragSystem.retrieveRelevantDocs(question, topK = 3)
        val docsContext = relevantDocs.joinToString("\n\n") { doc ->
            "Из ${doc.metadata["source"]}:\n${doc.text}"
        }

        // 2. Формируем system prompt с документацией
        val systemPrompt = buildString {
            appendLine("Ты - ассистент команды разработки продукта TaskFlow.")
            appendLine("Твоя задача - помогать команде управлять задачами, анализировать статус проекта и давать рекомендации.")
            appendLine()
            appendLine("=== ДОКУМЕНТАЦИЯ ===")
            appendLine(docsContext)
            appendLine()
            appendLine("Инструкции:")
            appendLine("1. Отвечай на русском языке")
            appendLine("2. Используй доступные инструменты MCP для получения актуальной информации о задачах и команде")
            appendLine("3. Если нужна информация о задачах - вызывай соответствующие инструменты")
            appendLine("4. При анализе приоритетов учитывай:")
            appendLine("   - Срочность (high/urgent приоритет)")
            appendLine("   - Дедлайны (dueDate)")
            appendLine("   - Блокирующие задачи (status=blocked)")
            appendLine("   - Зависимости между задачами")
            appendLine("5. Давай конкретные, actionable рекомендации")
            if (includeRecommendations) {
                appendLine("6. ОБЯЗАТЕЛЬНО дай рекомендации по приоритизации задач")
            }
        }

        // 3. Формируем user prompt
        var userPrompt = question
        if (userId != null) {
            userPrompt = "Вопрос про пользователя $userId: $question"
        }
        if (taskId != null) {
            userPrompt = "Вопрос про задачу $taskId: $question"
        }

        // 4. Генерируем ответ через llama3.2 с нативным tool calling
        logger.info { "🤖 Using llama3.2 with native MCP tool calling (temp: $temperature)" }
        val answer = ollamaClient.generateWithTools(
            userPrompt = userPrompt,
            systemPrompt = systemPrompt.trimIndent(),
            tools = mcpTools,
            toolExecutor = { toolName, arguments ->
                executeMcpTool(toolName, arguments)
            },
            model = "llama3.2",
            maxIterations = 10,
            temperature = temperature
        )

        logger.info { "✅ Generated answer (length: ${answer.length})" }
        return answer
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
                "get_user_tasks" -> {
                    val args = json.parseToJsonElement(arguments).jsonObject
                    val userId = args["userId"]?.jsonPrimitive?.content ?: ""
                    callMcpEndpoint("/api/get_user_tasks", """{"userId":"$userId"}""")
                }
                "get_task" -> {
                    val args = json.parseToJsonElement(arguments).jsonObject
                    val taskId = args["taskId"]?.jsonPrimitive?.content ?: ""
                    callMcpEndpoint("/api/get_task", """{"taskId":"$taskId"}""")
                }
                "search_tasks" -> {
                    callMcpEndpoint("/api/search_tasks", arguments)
                }
                "create_task" -> {
                    callMcpEndpoint("/api/create_task", arguments)
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
