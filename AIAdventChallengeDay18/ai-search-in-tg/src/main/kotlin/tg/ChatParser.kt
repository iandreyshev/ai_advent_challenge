package ru.iandreyshev.tg

import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import ru.iandreyshev.Message
import java.io.File
import kotlin.collections.plusAssign

class ChatParser {
    private val mapper = ObjectMapper().registerKotlinModule()

    fun parseMessages(jsonFile: File): List<Message> {
        val root = mapper.readTree(jsonFile)

        val messagesNode = when {
            root.has("messages") -> root["messages"]
            root.has("result") && root["result"].has("messages") -> root["result"]["messages"]
            else -> error("Cannot find messages array in JSON")
        }

        if (!messagesNode.isArray) error("messages is not an array")

        val out = ArrayList<Message>(messagesNode.size())
        for (m in messagesNode) {
            val id = m["id"]?.asLong() ?: continue
            val replyTo = m["reply_to_message_id"]?.takeIf { !it.isNull }?.asLong()

            val normalized = normalizeText(m["text"])
                .trim()
                .replace("\u0000", "")

            if (normalized.isBlank()) continue

            out += Message(
                id = id,
                text = normalized,
                replyToId = replyTo
            )
        }
        return out
    }

    private fun normalizeText(textNode: JsonNode?): String {
        if (textNode == null || textNode.isNull) return ""
        return when {
            textNode.isTextual -> textNode.asText()
            textNode.isArray -> buildString {
                for (el in textNode) {
                    when {
                        el.isTextual -> append(el.asText())
                        el.isObject -> {
                            val t = el["type"]?.asText()
                            val txt = el["text"]?.asText().orEmpty()
                            when (t) {
                                "text_link" -> {
                                    // Можно добавить href, но обычно достаточно текста (меньше шума в эмбеддингах)
                                    append(txt)
                                }
                                else -> append(txt)
                            }
                        }
                    }
                }
            }
            else -> ""
        }
    }
}