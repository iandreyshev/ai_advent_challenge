package ru.iandreyshev.assistant

import io.github.oshai.kotlinlogging.KotlinLogging
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.withContext
import java.io.File

private val logger = KotlinLogging.logger {}

class RAGSystem(
    private val ollamaClient: OllamaClient,
    private val vectorStore: VectorStore
) {
    suspend fun indexDocuments(docsDirectory: File) {
        if (!docsDirectory.exists() || !docsDirectory.isDirectory) {
            logger.error { "Directory does not exist: ${docsDirectory.absolutePath}" }
            return
        }

        val docFiles = docsDirectory.listFiles { file ->
            file.isFile && file.extension in listOf("txt", "md")
        } ?: emptyArray()

        logger.info { "📚 Indexing ${docFiles.size} documents..." }

        withContext(Dispatchers.IO) {
            docFiles.map { file ->
                async {
                    try {
                        indexDocument(file)
                    } catch (e: Exception) {
                        logger.error(e) { "Failed to index document: ${file.name}" }
                    }
                }
            }.awaitAll()
        }

        logger.info { "✅ Indexed ${vectorStore.size()} chunks" }
    }

    private suspend fun indexDocument(file: File) {
        val content = file.readText()
        val chunks = splitIntoChunks(content, chunkSize = 500, overlap = 50)

        chunks.forEachIndexed { index, chunkText ->
            val embedding = ollamaClient.generateEmbedding(chunkText)

            val chunk = DocumentChunk(
                id = "${file.nameWithoutExtension}_chunk_$index",
                text = chunkText,
                metadata = mapOf(
                    "source" to file.name,
                    "chunk_index" to index.toString()
                ),
                embedding = embedding
            )

            vectorStore.addDocument(chunk)
        }
    }

    suspend fun retrieveRelevantDocs(query: String, topK: Int = 3): List<DocumentChunk> {
        val queryEmbedding = ollamaClient.generateEmbedding(query)
        val results = vectorStore.search(queryEmbedding, topK)

        logger.info { "🔍 Found ${results.size} relevant docs (similarity: ${results.firstOrNull()?.similarity?.let { "%.2f".format(it) } ?: "N/A"})" }

        return results.map { it.chunk }
    }

    private fun splitIntoChunks(text: String, chunkSize: Int, overlap: Int): List<String> {
        val words = text.split(Regex("\\s+"))
        val chunks = mutableListOf<String>()

        var i = 0
        while (i < words.size) {
            val end = minOf(i + chunkSize, words.size)
            val chunk = words.subList(i, end).joinToString(" ")
            chunks.add(chunk)
            i += chunkSize - overlap
        }

        return chunks
    }

    fun buildPrompt(query: String, relevantDocs: List<DocumentChunk>): String {
        val context = relevantDocs.joinToString("\n\n") { doc ->
            "Документ: ${doc.metadata["source"]}\n${doc.text}"
        }

        return """
            Ты - ассистент поддержки пользователей продукта TaskFlow.

            Используй следующую информацию из документации для ответа на вопрос пользователя:

            $context

            Вопрос пользователя: $query

            Дай подробный и понятный ответ на русском языке, основываясь на предоставленной документации.
            Если информации недостаточно, так и скажи.
        """.trimIndent()
    }
}
