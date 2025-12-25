package ru.iandreyshev

data class Chunk(
    val chunkId: String,
    val messageIds: List<Long>,
    val text: String
)

data class IndexedChunk(
    val chunkId: String,
    val messageIds: List<Long>,
    val text: String,
    val embedding: FloatArray
)

data class ScoredCandidate(
    val chunk: IndexedChunk,
    val scoresByQuery: MutableMap<String, Double> = linkedMapOf(),
    var bestScore: Double = Double.NEGATIVE_INFINITY,
    var fusionScore: Double = 0.0
)

data class Message(
    val id: Long,
    val text: String,
    val replyToId: Long?
)

data class RankedPick(
    val chunkId: String,
    val evidence: String
)
