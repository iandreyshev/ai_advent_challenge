package ru.iandreyshev.assistant

import io.github.oshai.kotlinlogging.KotlinLogging
import kotlin.math.sqrt

private val logger = KotlinLogging.logger {}

data class DocumentChunk(
    val id: String,
    val text: String,
    val metadata: Map<String, String>,
    val embedding: List<Double>
)

data class SearchResult(
    val chunk: DocumentChunk,
    val similarity: Double
)

class VectorStore {
    private val documents = mutableListOf<DocumentChunk>()

    fun addDocument(chunk: DocumentChunk) {
        documents.add(chunk)
    }

    fun search(queryEmbedding: List<Double>, topK: Int = 3): List<SearchResult> {
        if (documents.isEmpty()) {
            logger.warn { "No documents in vector store" }
            return emptyList()
        }

        val results = documents.map { doc ->
            val similarity = cosineSimilarity(queryEmbedding, doc.embedding)
            SearchResult(doc, similarity)
        }
            .sortedByDescending { it.similarity }
            .take(topK)

        return results
    }

    fun size(): Int = documents.size

    private fun cosineSimilarity(a: List<Double>, b: List<Double>): Double {
        require(a.size == b.size) { "Vectors must have the same dimensions" }

        val dotProduct = a.zip(b).sumOf { (x, y) -> x * y }
        val magnitudeA = sqrt(a.sumOf { it * it })
        val magnitudeB = sqrt(b.sumOf { it * it })

        return if (magnitudeA == 0.0 || magnitudeB == 0.0) {
            0.0
        } else {
            dotProduct / (magnitudeA * magnitudeB)
        }
    }
}
