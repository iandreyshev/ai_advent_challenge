package ru.iandreyshev.rag

import ru.iandreyshev.Chunk
import ru.iandreyshev.IndexedChunk
import kotlin.math.roundToLong

class IndexBuilder(
    private val embedClient: OllamaEmbedClient
) {
    /**
     * @param reportEvery печатать прогресс каждые N чанков (например 10/20/50)
     */
    fun build(chunks: List<Chunk>, reportEvery: Int = 10): List<IndexedChunk> {
        val total = chunks.size
        if (total == 0) return emptyList()

        val startedAt = System.nanoTime()
        var lastReportAt = startedAt

        val out = ArrayList<IndexedChunk>(total)

        for ((i, c) in chunks.withIndex()) {
            val emb = embedClient.embed(c.text)
            out.add(
                IndexedChunk(
                    chunkId = c.chunkId,
                    messageIds = c.messageIds,
                    text = c.text,
                    embedding = emb
                )
            )

            val done = i + 1
            val shouldReport = (done % reportEvery == 0) || (done == total)
            if (shouldReport) {
                val now = System.nanoTime()
                val elapsedSec = (now - startedAt) / 1_000_000_000.0
                val avgPerItemSec = elapsedSec / done
                val remaining = total - done
                val etaSec = avgPerItemSec * remaining

                val speed = if (elapsedSec > 0) done / elapsedSec else 0.0
                val sinceLastReportSec = (now - lastReportAt) / 1_000_000_000.0

                println(
                    "Embedding: $done/$total " +
                            "(${(done * 100.0 / total).roundToLong()}%) " +
                            "avg=${"%.2f".format(avgPerItemSec)}s/item " +
                            "speed=${"%.2f".format(speed)} it/s " +
                            "ETA=${formatEta(etaSec)} " +
                            "(+${"%.1f".format(sinceLastReportSec)}s)"
                )
                lastReportAt = now
            }
        }

        return out
    }

    private fun formatEta(seconds: Double): String {
        val s = seconds.coerceAtLeast(0.0).roundToLong()
        val h = s / 3600
        val m = (s % 3600) / 60
        val sec = s % 60
        return when {
            h > 0 -> "${h}h ${m}m ${sec}s"
            m > 0 -> "${m}m ${sec}s"
            else -> "${sec}s"
        }
    }
}


//class IndexBuilder(
//    private val embedClient: OllamaEmbedClient
//) {
//    fun build(chunks: List<Chunk>): List<IndexedChunk> {
//        var timeToOneChunk = 0L
//
//        return chunks.mapIndexed { i, c ->
//            val startTime = System.currentTimeMillis()
//            val chunksLeft = chunks.size - i
//            val secondsToAll = timeToOneChunk * chunksLeft / 1000L
//
//            val minutesLeft = secondsToAll / 60
//            val secondsLeft = when (minutesLeft) {
//                0L -> 0L
//                else -> secondsToAll % minutesLeft
//            }
//
//            println("Chunks left: $chunksLeft ($minutesLeft:$secondsLeft)")
//
//            val emb = embedClient.embed(c.text)
//
//            IndexedChunk(
//                chunkId = c.chunkId,
//                messageIds = c.messageIds,
//                text = c.text,
//                embedding = emb
//            ).also {
//                timeToOneChunk = System.currentTimeMillis() - startTime
//            }
//        }
//    }
//}
