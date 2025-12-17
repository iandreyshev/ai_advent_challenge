package ru.iandreyshev

import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.types.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

fun buildMcpServer(): Server {
    val ispring = ISpringLearnClient(
        apiHost = Secrets.API_HOST,
        clientId = Secrets.ISPRING_CLIENT_ID,
        clientSecret = Secrets.ISPRING_CLIENT_SECRET
    )

    val server = Server(
        serverInfo = Implementation(
            name = "ispring-learn-mcp",
            version = "1.0.0",
            title = "iSpring Learn MCP Server"
        ),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    // MCP Tool: get_users
    // args (optional):
    //   departments: "id1,id2"
    //   groups: "id1,id2"
    //   accept: "application/json" (default) or "application/xml"
    server.addTool(
        name = "get_users",
        description = "Получить список пользователей из iSpring Learn (REST GET /user)"
    ) { request ->
        val departments = request.arguments?.get("departments")?.toString()
        val groups = request.arguments?.get("groups")?.toString()
        val accept = request.arguments?.get("accept")?.toString() ?: "application/json"

        val body = withContext(Dispatchers.IO) {
            ispring.getUsers(
                departmentsCsv = departments,
                groupsCsv = groups,
                accept = accept
            )
        }

        CallToolResult(
            content = listOf(TextContent(body))
        )
    }

    // MCP Tool: get_user_info
    // args:
    //   user_id: "uuid" (required)
    //   accept: "application/json" (default) or "application/xml"
    server.addTool(
        name = "get_user_info",
        description = "Получить информацию о пользователе по user_id из iSpring Learn (REST GET /user/{user_id})"
    ) { request ->
        val userId = request.arguments?.get("user_id")?.toString()?.trim().orEmpty()
        if (userId.isBlank()) {
            return@addTool CallToolResult(
                isError = true,
                content = listOf(TextContent("Missing required argument: user_id"))
            )
        }

        val accept = request.arguments?.get("accept")?.toString() ?: "application/json"

        val body = withContext(Dispatchers.IO) {
            ispring.getUserInfo(
                userId = userId,
                accept = accept
            )
        }

        CallToolResult(
            content = listOf(TextContent(body))
        )
    }

    return server
}
