package ru.iandreyshev.ai

import ru.iandreyshev.RankedPick
import ru.iandreyshev.ScoredCandidate

interface LlmClient {
    /**
     * Сгенерировать ровно 3 переформулировки вопроса
     */
    fun rewriteQueries(question: String): List<String>

    /**
     * Выбрать лучшие chunkId из кандидатов
     */
    fun rankChunks(
        queries: List<String>,
        candidates: List<ScoredCandidate>,
        finalTopN: Int
    ): List<RankedPick>
}