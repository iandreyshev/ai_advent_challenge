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
        val docsPath = "../hotels-mcp/src/main/resources/docs"
        val docsDir = File(docsPath)

        if (!docsDir.exists()) {
            logger.error { "Documentation directory not found: ${docsDir.absolutePath}" }
            logger.error { "Please ensure the docs are in the correct location" }
            return@runBlocking
        }

        logger.info { "Indexing documentation from: ${docsDir.absolutePath}" }
        ragSystem.indexDocuments(docsDir)

        logger.info { "" }
        logger.info { "🚀 Support Assistant ready with:" }
        logger.info { "   • RAG: ${vectorStore.size()} chunks indexed" }
        logger.info { "   • MCP: Tool calling enabled" }
        logger.info { "   • LLM: llama3.1 via Ollama" }
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
            question = "Почему не работает авторизация через Google?",
            userId = "user001",
            ticketId = "ticket001"
        ),
        TestQuery(
            question = "Не могу создать задачу, кнопка не работает",
            userId = "user002",
            ticketId = "ticket002"
        ),
        TestQuery(
            question = "Не приходят уведомления на email",
            userId = "user003",
            ticketId = "ticket003"
        )
    )

    testQueries.forEach { query ->
        logger.info { "=" .repeat(60) }
        logger.info { "📝 ВОПРОС: ${query.question}" }
        logger.info { "   User: ${query.userId}, Ticket: ${query.ticketId}" }
        logger.info { "" }

        try {
            val answer = assistant.answerQuestion(
                question = query.question,
                userId = query.userId,
                ticketId = query.ticketId
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
    val ticketId: String?
)
