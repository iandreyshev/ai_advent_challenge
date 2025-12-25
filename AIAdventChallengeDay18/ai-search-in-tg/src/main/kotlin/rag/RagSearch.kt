package ru.iandreyshev.rag

import ru.iandreyshev.IndexedChunk
import ru.iandreyshev.ScoredCandidate
import ru.iandreyshev.ai.LlmClient
import kotlin.math.sqrt

class RagSearch(
    private val embedClient: OllamaEmbedClient,
    private val llm: LlmClient,
    private val index: List<IndexedChunk>,
    private val chatId: String,
    private val topKPerQuery: Int = 4,
    private val finalTopN: Int = 5
) {

    fun answerCandidates(question: String): List<String> {
        // 1) 3 переформулировки через LLM
        val rewrites = llm.rewriteQueries(question)
//        require(rewrites.size == 3) { "Expected 3 rewrites, got ${rewrites.size}" }

        val queries = listOf(question) + rewrites

        // 2) эмбеддим 4 запроса
        val queryEmbeds = queries.associateWith { q -> embedClient.embed(q) }

        // 3) retrieve topK per query
        val candidatesByChunkId = linkedMapOf<String, ScoredCandidate>()

        // --- (4) RRF aggregation (stable vs noisy rewrites) ---
        val rrfByChunkId = linkedMapOf<String, Double>()
        val rrfK = 60.0 // typical constant for RRF

        queries.forEach { q ->
            val qEmb = queryEmbeds.getValue(q)
            val top = topK(index, topKPerQuery) { ch ->
                cosineSimilarity(qEmb, ch.embedding)
            }

            for ((rank0, pair) in top.withIndex()) {
                val (chunk, score) = pair
                val rank = rank0 + 1

                val cand = candidatesByChunkId.getOrPut(chunk.chunkId) {
                    ScoredCandidate(chunk = chunk)
                }
                cand.scoresByQuery[q] = score
                if (score > cand.bestScore) cand.bestScore = score

                // RRF: sum(1 / (k + rank))
                val add = 1.0 / (rrfK + rank)
                rrfByChunkId[chunk.chunkId] = (rrfByChunkId[chunk.chunkId] ?: 0.0) + add
            }
        }

        val candidates = candidatesByChunkId.values
            .onEach { c -> c.fusionScore = rrfByChunkId[c.chunk.chunkId] ?: 0.0 }
            .sortedByDescending { it.fusionScore }
            .toList()

        // 4) LLM rerank: returns chunkId + evidence
        val picked = llm.rankChunks(
            queries = queries,
            candidates = candidates,
            finalTopN = finalTopN
        )

        // safety: фильтруем неизвестные + берём только валидные chunkId
        val existing = picked
            .map { it.chunkId }
            .filter { id -> candidatesByChunkId.containsKey(id) }
            .distinct()

        val finalIds = if (existing.size >= finalTopN) {
            existing.take(finalTopN)
        } else {
            val fallback = candidates
                .sortedByDescending { it.fusionScore }
                .map { it.chunk.chunkId }
                .filterNot { it in existing }
                .take(finalTopN - existing.size)

            (existing + fallback).take(finalTopN)
        }

        // 5) возвращаем ссылки по первому messageId в чанке
        return finalIds.mapNotNull { id ->
            val ch = candidatesByChunkId[id]?.chunk ?: return@mapNotNull null
            val msgId = ch.messageIds.firstOrNull() ?: return@mapNotNull null
            "https://t.me/$chatId/$msgId"
        }
    }
}

private fun cosineSimilarity(a: FloatArray, b: FloatArray): Double {
    require(a.size == b.size) { "Embeddings dimension mismatch: ${a.size} vs ${b.size}" }

    var dot = 0.0
    var na = 0.0
    var nb = 0.0

    for (i in a.indices) {
        val x = a[i].toDouble()
        val y = b[i].toDouble()
        dot += x * y
        na += x * x
        nb += y * y
    }

    val denom = sqrt(na) * sqrt(nb)

    return if (denom == 0.0) 0.0 else dot / denom
}

private fun <T> topK(items: List<T>, k: Int, score: (T) -> Double): List<Pair<T, Double>> {
    return items
        .asSequence()
        .map { it to score(it) }
        .sortedByDescending { it.second }
        .take(k)
        .toList()
}
