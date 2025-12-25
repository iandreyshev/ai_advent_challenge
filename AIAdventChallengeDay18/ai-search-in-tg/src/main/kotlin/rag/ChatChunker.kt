package ru.iandreyshev.rag

import ru.iandreyshev.Chunk
import ru.iandreyshev.Message
import kotlin.collections.plusAssign

class ChatChunker(
    private val maxMessages: Int = 12,
    private val overlap: Int = 4,
    private val maxChunkChars: Int
) {
    init {
        require(maxMessages > 0)
        require(overlap in 0 until maxMessages)
        require(maxChunkChars > 200)
    }

    private val maxMessageChars = maxChunkChars - 100

    fun chunk(messages: List<Message>): List<Chunk> {
        if (messages.isEmpty()) return emptyList()

        val byId = messages.associateBy { it.id }
        val chunks = mutableListOf<Chunk>()

        var start = 0
        while (start < messages.size) {
            val (chunk, endExclusive) = buildChunk(messages, byId, start) ?: break
            chunks += chunk

            if (endExclusive >= messages.size) break

            // overlap по сообщениям
            start = (endExclusive - overlap).coerceAtLeast(start + 1)
        }

        return chunks
    }

    private fun buildChunk(
        messages: List<Message>,
        byId: Map<Long, Message>,
        start: Int
    ): Pair<Chunk, Int>? {
        if (start >= messages.size) return null

        val messageIds = ArrayList<Long>(maxMessages)
        val includedParents = HashSet<Long>(maxMessages)

        val sb = StringBuilder()
        var i = start

        while (i < messages.size && messageIds.size < maxMessages) {
            val msg = messages[i]

            // Сформируем блок текста для одного сообщения (с reply_to родителем, если есть)
            val block = buildString {
//                val parentId = msg.replyToId

//                if (parentId != null && !includedParents.contains(parentId)) {
//                    val parent = byId[parentId]
//                    val pText = parent?.text?.trim().orEmpty()
//
//                    if (pText.isNotBlank()) {
//                        includedParents.add(parentId)
//
//                        append(pText.take(maxMessageChars))
//                        append('\n')
//                    }
//                }

                val mText = msg.text.trim()

                if (mText.isNotBlank()) {
                    append(mText.take(maxMessageChars))
                    append('\n')
                }
            }

            // если блок пустой — пропускаем сообщение
            if (block.isBlank()) {
                i++
                continue
            }

            // Проверяем лимит по длине чанка:
            // если уже есть что-то в чанке и добавление блока превысит maxChunkChars — останавливаемся
            if (sb.isNotEmpty() && sb.length + block.length > maxChunkChars) {
                break
            }

            // Если чанк пустой и даже один block слишком длинный —
            // добавим его в урезанном виде (чтобы не зациклиться)
            if (sb.isEmpty() && block.length > maxChunkChars) {
                sb.append(block.take(maxChunkChars))
                messageIds.add(msg.id)
                i++ // мы потребили сообщение
                break
            }

            // Добавляем блок
            sb.append(block)
            messageIds.add(msg.id)
            i++
        }

        if (messageIds.isEmpty()) return null

        val chunkText = sb.toString().trim()
        val chunkId = "${messageIds.first()}-${messageIds.last()}"

        return Chunk(
            chunkId = chunkId,
            messageIds = messageIds,
            text = chunkText
        ) to i
    }
}
