package ru.iandreyshev

import ru.iandreyshev.ai.YandexLlmClient
import ru.iandreyshev.rag.*
import ru.iandreyshev.tg.ChatParser
import ru.iandreyshev.utils.Secrets
import ru.iandreyshev.utils.loadSecrets
import java.io.File

private const val CHAT_JSON_PATH = "result.json"
private const val INDEX_JSONL_PATH = "index.jsonl"
private const val SECRETS_PATH = "secrets.properties"

private const val N_MESSAGES_PER_CHUNK = 12
private const val MAX_CHUNK_CHARS = 2500
private const val CHUNK_OVERLAP = 4
private const val TOP_K_PER_QUERY = 50
private const val FINAL_TOP_N = 5

private const val OLLAMA_EMBED_MODEL = "snowflake-arctic-embed2:latest"
private const val OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"

private const val TELEGRAM_CHAT_ID = "chat_hotel"

fun main(args: Array<String>) {
    val secrets = loadSecrets(SECRETS_PATH)
    val indexFile = File(INDEX_JSONL_PATH)
    val shouldBuildIndex = args.any { it == "--build-index" || it == "-i" }

    if (shouldBuildIndex) {
        buildIndex(secrets, indexFile)
    }

    require(indexFile.exists()) {
        "Index file not found: ${indexFile.absolutePath}. Run with --build-index first."
    }

    runSearch(secrets, indexFile)
}

private fun buildIndex(secrets: Secrets, indexFile: File) {
    val chatFile = File(CHAT_JSON_PATH)

    require(chatFile.exists()) { "Chat file not found: ${chatFile.absolutePath}" }
    println("Building index from ${chatFile.name} -> ${indexFile.name}")

    val parser = ChatParser()
    val messages = parser.parseMessages(chatFile)

    val chunker = ChatChunker(
        maxMessages = N_MESSAGES_PER_CHUNK,
        overlap = CHUNK_OVERLAP,
        maxChunkChars = MAX_CHUNK_CHARS
    )
    val chunks = chunker.chunk(messages)

    val embed = OllamaEmbedClient(
        embedUrl = OLLAMA_EMBED_URL,
        model = OLLAMA_EMBED_MODEL
    )

    val indexed = IndexBuilder(embed).build(chunks)

    JsonlIndex.writeAll(indexed, indexFile)

    println("OK: messages=${messages.size}, chunks=${chunks.size}, index=${indexFile.name}")
}

private fun runSearch(secrets: Secrets, indexFile: File) {
    val embed = OllamaEmbedClient(
        embedUrl = OLLAMA_EMBED_URL,
        model = OLLAMA_EMBED_MODEL
    )
    val yandexllm = YandexLlmClient(
        folderId = secrets.yandexFolderId,
        apiKey = secrets.yandexApiKey,
        agentId = secrets.yandexAgentId
    )
    val indexedChunks = JsonlIndex.readAll(indexFile)
    val rag = RagSearch(
        embedClient = embed,
        llm = yandexllm,
        index = indexedChunks,
        chatId = TELEGRAM_CHAT_ID,
        topKPerQuery = TOP_K_PER_QUERY,
        finalTopN = FINAL_TOP_N
    )

    println("Chat mode. Type your question. Commands: /exit, /help")
    while (true) {
        print("> ")
        val line = readlnOrNull() ?: break
        val q = line.trim()
        if (q.isBlank()) continue

        when (q.lowercase()) {
            "/exit" -> return
            "/help" -> {
                println(
                    """
Commands:
  /exit  - quit
  /help  - show this help

Notes:
  - It returns top-$FINAL_TOP_N message links from the chat index.
  - Rebuild index: run program with --build-index
""".trimIndent()
                )
                continue
            }
        }

        try {
            val links = rag.answerCandidates(q)
            println("ТОП-5 результатов по запросу \"$q\":")
            links.forEachIndexed { i, r ->
                println("${i + 1}. $r")
            }
        } catch (e: Exception) {
            System.err.println("Error: ${e.message}")
        }
    }
}