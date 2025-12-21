package ru.iandreyshev

import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.types.CallToolResult
import io.modelcontextprotocol.kotlin.sdk.types.Implementation
import io.modelcontextprotocol.kotlin.sdk.types.ServerCapabilities
import io.modelcontextprotocol.kotlin.sdk.types.TextContent
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.time.Instant

// Папка, где лежит docker-compose.yml
private val DOCKER_PROJECT_DIR = File("/root/ai_advent_challenge/docker-web")

fun buildMcpServer(): Server {
    val server = Server(
        serverInfo = Implementation(
            name = "docker-toggle-mcp",
            version = "1.0.0",
            title = "Docker Toggle MCP Server"
        ),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    server.addTool(
        name = "start_docker_server",
        description = "Запустить docker compose (web-сервер) в папке проекта и поднять HTML на порту 8080"
    ) { _ ->
        val result = withContext(Dispatchers.IO) {
            runComposeCommand(
                projectDir = DOCKER_PROJECT_DIR,
                args = listOf("up", "-d")
            )
        }

        CallToolResult(
            content = listOf(TextContent(result))
        )
    }

    server.addTool(
        name = "stop_docker_server",
        description = "Остановить web-сервер: docker compose down в папке проекта"
    ) { _ ->
        val result = withContext(Dispatchers.IO) {
            runComposeCommand(
                projectDir = DOCKER_PROJECT_DIR,
                args = listOf("down")
            )
        }

        CallToolResult(
            content = listOf(TextContent(result))
        )
    }

    return server
}

private fun runComposeCommand(projectDir: File, args: List<String>): String {
    if (!projectDir.exists() || !projectDir.isDirectory) {
        return """{"ok":false,"error":"Project dir not found: ${escapeJson(projectDir.absolutePath)}"}"""
    }

    // Важно: на VPS обычно есть docker compose plugin -> команда: `docker compose ...`
    val cmd = listOf("docker", "compose") + args

    return try {
        val pb = ProcessBuilder(cmd)
            .directory(projectDir)
            .redirectErrorStream(true)

        val p = pb.start()
        val out = p.inputStream.bufferedReader().readText()
        val code = p.waitFor()

        """{
          "ok":${code == 0},
          "exitCode":$code,
          "cmd":"${escapeJson(cmd.joinToString(" "))}",
          "cwd":"${escapeJson(projectDir.absolutePath)}",
          "ts":"${escapeJson(Instant.now().toString())}",
          "output":"${escapeJson(out)}"
        }""".trimIndent()
    } catch (e: Exception) {
        """{
          "ok":false,
          "error":"${escapeJson(e::class.qualifiedName ?: "Exception")}: ${escapeJson(e.message ?: "")}"
        }""".trimIndent()
    }
}

private fun escapeJson(s: String): String =
    s.replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
