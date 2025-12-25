package ru.iandreyshev.rag

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import ru.iandreyshev.IndexedChunk
import java.io.File
import kotlin.collections.plusAssign

object JsonlIndex {
    private val mapper = ObjectMapper().registerKotlinModule()

    fun writeAll(indexedChunks: List<IndexedChunk>, outFile: File) {
        outFile.parentFile?.mkdirs()
        outFile.bufferedWriter().use { w ->
            for (c in indexedChunks) {
                val row = mapOf(
                    "chunkId" to c.chunkId,
                    "messageIds" to c.messageIds,
                    "text" to c.text,
                    "embedding" to c.embedding.toList()
                )
                w.append(mapper.writeValueAsString(row)).append('\n')
            }
        }
    }

    fun readAll(file: File): List<IndexedChunk> {
        val out = ArrayList<IndexedChunk>()
        file.forEachLine { line ->
            if (line.isBlank()) return@forEachLine
            val n = mapper.readTree(line)

            val chunkId = n["chunkId"].asText()
            val messageIds = n["messageIds"].map { it.asLong() }
            val text = n["text"].asText()

            val embNode = n["embedding"]
            val emb = FloatArray(embNode.size())
            for (i in 0 until embNode.size()) emb[i] = embNode[i].asDouble().toFloat()

            out += IndexedChunk(chunkId, messageIds, text, emb)
        }
        return out
    }
}
