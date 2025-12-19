package ru.iandreyshev

import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.modelcontextprotocol.kotlin.sdk.server.mcp

fun Application.configureRouting() {
    install(io.ktor.server.sse.SSE)

    routing {
        mcp {
            buildMcpServer()
        }
    }
}