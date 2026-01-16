package ru.iandreyshev.assistant

import io.github.oshai.kotlinlogging.KotlinLogging
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.HttpTimeout
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import java.io.File

private val logger = KotlinLogging.logger {}

fun main() = runBlocking {
    logger.info { "🎯 Starting TaskFlow Support Assistant" }

    // Создаем HTTP клиент
    val httpClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                prettyPrint = true
            })
        }
        install(HttpTimeout) {
            requestTimeoutMillis = 60000 // 60 секунд для генерации ответа
            connectTimeoutMillis = 10000  // 10 секунд для подключения
            socketTimeoutMillis = 60000   // 60 секунд для чтения данных
        }
    }

    try {
        // Инициализируем компоненты
        val ollamaClient = OllamaClient(httpClient)

        // Проверяем доступность Ollama
        if (!ollamaClient.checkHealth()) {
            logger.error { "Ollama is not available. Please start Ollama first." }
            logger.error { "Run: ollama serve" }
            logger.error { "And pull model: ollama pull nomic-embed-text" }
            return@runBlocking
        }

        logger.info { "Ollama is available" }

        // Создаем векторное хранилище и RAG систему
        val vectorStore = VectorStore()
        val ragSystem = RAGSystem(ollamaClient, vectorStore)

        // Индексируем документацию
        // Путь к документации - используем документы из MCP сервера
        val docsPath = "../tasks-mcp/src/main/resources/docs"
        val docsDir = File(docsPath)

        if (!docsDir.exists()) {
            logger.error { "Documentation directory not found: ${docsDir.absolutePath}" }
            logger.error { "Please ensure the docs are in the correct location" }
            return@runBlocking
        }

        logger.info { "Indexing documentation from: ${docsDir.absolutePath}" }
        ragSystem.indexDocuments(docsDir)

        logger.info { "" }
        logger.info { "🚀 TaskFlow Team Assistant ready with:" }
        logger.info { "   • RAG: ${vectorStore.size()} chunks indexed" }
        logger.info { "   • MCP: 5 tools connected natively to LLM" }
        logger.info { "     - get_user_info" }
        logger.info { "     - get_task" }
        logger.info { "     - get_user_tasks" }
        logger.info { "     - search_tasks" }
        logger.info { "     - create_task" }
        logger.info { "   • LLM: llama3.2 via Ollama (native tool calling)" }
        logger.info { "" }
        logger.info { "=" .repeat(60) }

        // Создаем ассистента
        val assistant = SupportAssistant(
            ragSystem = ragSystem,
            ollamaClient = ollamaClient,
            httpClient = httpClient
        )

        // Примеры вопросов для тестирования
        testAssistant(assistant)

    } catch (e: Exception) {
        logger.error(e) { "Failed to start Support Assistant" }
    } finally {
        httpClient.close()
    }
}

suspend fun testAssistant(assistant: SupportAssistant) {
    logger.info { "Running test queries..." }
    logger.info { "" }

    val testQueries = listOf(
        TestQuery(
            question = "Покажи задачи с приоритетом high и предложи, что делать первым",
            userId = null,
            taskId = null,
            includeRecommendations = true,
            temperature = 0.7  // Сбалансированная температура для рекомендаций
        ),
        TestQuery(
            question = "Какие задачи у Ивана Петрова? Что он сейчас делает?",
            userId = "user001",
            taskId = null,
            includeRecommendations = false,
            temperature = 0.3  // Низкая температура для фактических данных
        ),
        TestQuery(
            question = "Расскажи про задачу task001 - что там с багом OAuth?",
            userId = null,
            taskId = "task001",
            includeRecommendations = false,
            temperature = 0.5  // Средняя температура для объяснений
        ),
        TestQuery(
            question = "Какой статус проекта TaskFlow Core? Есть ли проблемные задачи?",
            userId = null,
            taskId = null,
            includeRecommendations = true,
            temperature = 0.8  // Повышенная температура для креативного анализа
        ),
        TestQuery(
            question = "Какие задачи заблокированы и почему?",
            userId = null,
            taskId = null,
            includeRecommendations = true,
            temperature = 0.6  // Умеренная температура для аналитики
        )
    )

    testQueries.forEach { query ->
        logger.info { "=" .repeat(60) }
        logger.info { "📝 ВОПРОС: ${query.question}" }
        if (query.userId != null) logger.info { "   User: ${query.userId}" }
        if (query.taskId != null) logger.info { "   Task: ${query.taskId}" }
        logger.info { "   Temperature: ${query.temperature}" }
        logger.info { "" }

        try {
            val answer = assistant.answerQuestion(
                question = query.question,
                userId = query.userId,
                taskId = query.taskId,
                includeRecommendations = query.includeRecommendations,
                temperature = query.temperature
            )

            logger.info { "" }
            logger.info { "💬 ОТВЕТ:" }
            logger.info { answer }
        } catch (e: Exception) {
            logger.error(e) { "❌ Failed to answer question" }
        }

        logger.info { "=" .repeat(60) }
        logger.info { "" }

        // Пауза между запросами
        kotlinx.coroutines.delay(2000)
    }

    logger.info { "✅ All test queries completed" }
}

data class TestQuery(
    val question: String,
    val userId: String?,
    val taskId: String?,
    val includeRecommendations: Boolean = false,
    val temperature: Double = 0.7
)
