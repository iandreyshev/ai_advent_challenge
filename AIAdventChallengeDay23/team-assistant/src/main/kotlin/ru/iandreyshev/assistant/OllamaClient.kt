package ru.iandreyshev.assistant

import io.github.oshai.kotlinlogging.KotlinLogging
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

private val logger = KotlinLogging.logger {}

@Serializable
data class OllamaEmbeddingRequest(
    val model: String,
    val prompt: String
)

@Serializable
data class OllamaEmbeddingResponse(
    val embedding: List<Double>
)

@Serializable
data class OllamaGenerateRequest(
    val model: String,
    val prompt: String,
    val stream: Boolean = false,
    val options: Map<String, Double>? = null
)

@Serializable
data class OllamaGenerateResponse(
    val model: String,
    val created_at: String,
    val response: String,
    val done: Boolean
)

// Для Chat API с tool calling
@Serializable
data class OllamaChatRequest(
    val model: String,
    val messages: List<ChatMessage>,
    val tools: List<ToolDefinition>? = null,
    val stream: Boolean = false,
    val options: Map<String, Double>? = null
)

@Serializable
data class ChatMessage(
    val role: String, // "system", "user", "assistant", "tool"
    val content: String,
    val tool_calls: List<ToolCall>? = null
)

@Serializable
data class ToolDefinition(
    val type: String = "function",
    val function: FunctionDefinition
)

@Serializable
data class FunctionDefinition(
    val name: String,
    val description: String,
    val parameters: ToolParameters
)

@Serializable
data class ToolParameters(
    val type: String = "object",
    val properties: Map<String, PropertyDefinition>,
    val required: List<String>
)

@Serializable
data class PropertyDefinition(
    val type: String,
    val description: String
)

@Serializable
data class ToolCall(
    val id: String,
    val type: String = "function",
    val function: FunctionCall
)

@Serializable
data class FunctionCall(
    val name: String,
    val arguments: kotlinx.serialization.json.JsonElement // JSON объект или строка
)

@Serializable
data class OllamaChatResponse(
    val model: String,
    val created_at: String,
    val message: ChatMessage,
    val done: Boolean
)

class OllamaClient(
    private val httpClient: HttpClient,
    private val baseUrl: String = "http://localhost:11434",
    private val embeddingModel: String = "nomic-embed-text"
) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun generateEmbedding(text: String): List<Double> {
        val response: HttpResponse = httpClient.post("$baseUrl/api/embeddings") {
            contentType(ContentType.Application.Json)
            setBody(
                json.encodeToString(
                    OllamaEmbeddingRequest.serializer(),
                    OllamaEmbeddingRequest(
                        model = embeddingModel,
                        prompt = text
                    )
                )
            )
        }

        val responseBody = response.bodyAsText()
        val embeddingResponse = json.decodeFromString<OllamaEmbeddingResponse>(responseBody)

        return embeddingResponse.embedding
    }

    suspend fun generateResponse(
        prompt: String,
        model: String = "llama3",
        temperature: Double? = null
    ): String {
        logger.info { "Generating response with model: $model, temperature: $temperature" }

        val options = temperature?.let { mapOf("temperature" to it) }

        val response: HttpResponse = httpClient.post("$baseUrl/api/generate") {
            contentType(ContentType.Application.Json)
            setBody(
                json.encodeToString(
                    OllamaGenerateRequest.serializer(),
                    OllamaGenerateRequest(
                        model = model,
                        prompt = prompt,
                        stream = false,
                        options = options
                    )
                )
            )
        }

        val responseBody = response.bodyAsText()

        // Ollama может возвращать streaming ответ даже с stream=false
        // Парсим построчно и собираем полный ответ
        val fullResponse = StringBuilder()
        responseBody.lines().forEach { line ->
            if (line.isNotBlank()) {
                try {
                    val chunk = json.decodeFromString<OllamaGenerateResponse>(line)
                    fullResponse.append(chunk.response)
                } catch (e: Exception) {
                    // Игнорируем ошибки парсинга отдельных строк
                }
            }
        }

        return fullResponse.toString()
    }

    suspend fun generateWithTools(
        userPrompt: String,
        systemPrompt: String,
        tools: List<ToolDefinition>,
        toolExecutor: suspend (String, String) -> String, // (toolName, arguments) -> result
        model: String = "llama3.1",
        maxIterations: Int = 5,
        temperature: Double? = null
    ): String {
        logger.info { "🔧 Generating response with tool calling support (temp: $temperature)" }

        val messages = mutableListOf(
            ChatMessage(role = "system", content = systemPrompt),
            ChatMessage(role = "user", content = userPrompt)
        )

        val options = temperature?.let { mapOf("temperature" to it) }

        var iteration = 0
        while (iteration < maxIterations) {
            iteration++

            val response: HttpResponse = httpClient.post("$baseUrl/api/chat") {
                contentType(ContentType.Application.Json)
                setBody(
                    json.encodeToString(
                        OllamaChatRequest.serializer(),
                        OllamaChatRequest(
                            model = model,
                            messages = messages,
                            tools = tools,
                            stream = false,
                            options = options
                        )
                    )
                )
            }

            val responseBody = response.bodyAsText()

            // Parse streaming response
            // Ollama возвращает несколько JSON объектов построчно
            var messageWithToolCalls: ChatMessage? = null
            val contentBuilder = StringBuilder()
            var lastResponse: OllamaChatResponse? = null

            responseBody.lines().forEach { line ->
                if (line.isNotBlank()) {
                    try {
                        val response = json.decodeFromString<OllamaChatResponse>(line)
                        lastResponse = response

                        // Сохраняем сообщение с tool_calls (обычно в первом чанке)
                        if (response.message.tool_calls?.isNotEmpty() == true) {
                            messageWithToolCalls = response.message
                            logger.debug { "Found tool_calls in response chunk" }
                        }

                        // Собираем контент из всех чанков
                        if (response.message.content.isNotBlank()) {
                            contentBuilder.append(response.message.content)
                        }
                    } catch (e: Exception) {
                        logger.warn { "Failed to parse line: $line - ${e.message}" }
                    }
                }
            }

            // Определяем финальное сообщение
            val assistantMessage = when {
                // Если есть tool_calls - используем их (приоритет)
                messageWithToolCalls != null -> messageWithToolCalls!!
                // Если есть собранный контент - создаем сообщение с ним
                contentBuilder.isNotEmpty() -> ChatMessage(
                    role = "assistant",
                    content = contentBuilder.toString()
                )
                // Fallback на последнее сообщение
                lastResponse?.message != null -> lastResponse!!.message
                // Ошибка если ничего не распарсилось
                else -> {
                    logger.error { "Failed to parse chat response from body:\n$responseBody" }
                    return "Ошибка при получении ответа от модели"
                }
            }

            messages.add(assistantMessage)

            // Проверяем есть ли tool calls
            val toolCalls = assistantMessage.tool_calls
            if (toolCalls.isNullOrEmpty()) {
                // Нет tool calls - возвращаем финальный ответ
                logger.info { "✅ Generated final answer (no more tool calls)" }
                return assistantMessage.content
            }

            // Выполняем tool calls
            logger.info { "🔧 Model decided to call ${toolCalls.size} tool(s)" }
            for (toolCall in toolCalls) {
                val toolName = toolCall.function.name
                val argumentsJson = toolCall.function.arguments

                // Преобразуем JsonElement в строку для передачи в toolExecutor
                val argumentsString = when (argumentsJson) {
                    is kotlinx.serialization.json.JsonObject -> argumentsJson.toString()
                    is kotlinx.serialization.json.JsonPrimitive -> argumentsJson.content
                    else -> argumentsJson.toString()
                }

                logger.info { "  → Executing: $toolName($argumentsString)" }

                try {
                    val result = toolExecutor(toolName, argumentsString)
                    logger.info { "  ✓ Tool result: ${result.take(100)}${if (result.length > 100) "..." else ""}" }

                    // Добавляем результат как tool message
                    messages.add(
                        ChatMessage(
                            role = "tool",
                            content = result
                        )
                    )
                } catch (e: Exception) {
                    logger.error(e) { "  ✗ Failed to execute tool: $toolName" }
                    val errorMessage = "{\"error\": \"${e.message?.replace("\"", "\\\"")}\"}"
                    messages.add(
                        ChatMessage(
                            role = "tool",
                            content = errorMessage
                        )
                    )
                }
            }
        }

        logger.warn { "Max iterations reached" }
        return messages.lastOrNull { it.role == "assistant" }?.content
            ?: "Не удалось получить ответ"
    }

    suspend fun checkHealth(): Boolean {
        return try {
            val response: HttpResponse = httpClient.get("$baseUrl/api/tags")
            response.status.isSuccess()
        } catch (e: Exception) {
            logger.error(e) { "Failed to check Ollama health" }
            false
        }
    }
}
