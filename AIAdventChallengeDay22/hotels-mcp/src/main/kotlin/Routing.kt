package ru.iandreyshev

import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.modelcontextprotocol.kotlin.sdk.server.mcp
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable
data class UserInfoResponse(
    val id: String,
    val email: String,
    val name: String,
    val registeredAt: String,
    val plan: String,
    val status: String
)

@Serializable
data class TicketResponse(
    val id: String,
    val userId: String,
    val userEmail: String,
    val userName: String,
    val userPlan: String,
    val subject: String,
    val description: String,
    val status: String,
    val priority: String,
    val category: String,
    val createdAt: String,
    val updatedAt: String,
    val tags: List<String>,
    val resolution: String?
)

@Serializable
data class UserTicketResponse(
    val id: String,
    val subject: String,
    val description: String,
    val status: String,
    val priority: String,
    val category: String,
    val createdAt: String,
    val updatedAt: String,
    val tags: List<String>
)

fun Application.configureRouting() {
    install(io.ktor.server.sse.SSE)
    install(io.ktor.server.plugins.contentnegotiation.ContentNegotiation) {
        json()
    }

    val supportData = loadSupportDataFromJson("/support.json")

    routing {
        // MCP SDK endpoint (для интеграции с Яндекс-агентом)
        mcp {
            buildMcpServer()
        }

        // REST API endpoints (для демо и тестирования)
        route("/api") {
            post("/get_user_info") {
                val body = call.receiveText()
                val json = Json.parseToJsonElement(body).jsonObject
                val userId = json["userId"]?.jsonPrimitive?.content ?: ""

                val user = supportData.users.firstOrNull {
                    it.id.equals(userId, ignoreCase = true) ||
                            it.email.equals(userId, ignoreCase = true)
                }

                if (user == null) {
                    call.respond(HttpStatusCode.NotFound, mapOf("error" to "user not found"))
                } else {
                    call.respond(
                        UserInfoResponse(
                            id = user.id,
                            email = user.email,
                            name = user.name,
                            registeredAt = user.registeredAt,
                            plan = user.plan,
                            status = user.status
                        )
                    )
                }
            }

            post("/get_ticket") {
                val body = call.receiveText()
                val json = Json.parseToJsonElement(body).jsonObject
                val ticketId = json["ticketId"]?.jsonPrimitive?.content ?: ""

                val ticket = supportData.tickets.firstOrNull {
                    it.id.equals(ticketId, ignoreCase = true)
                }

                if (ticket == null) {
                    call.respond(HttpStatusCode.NotFound, mapOf("error" to "ticket not found"))
                } else {
                    val user = supportData.users.firstOrNull { it.id == ticket.userId }
                    call.respond(
                        TicketResponse(
                            id = ticket.id,
                            userId = ticket.userId,
                            userEmail = user?.email ?: "unknown",
                            userName = user?.name ?: "unknown",
                            userPlan = user?.plan ?: "unknown",
                            subject = ticket.subject,
                            description = ticket.description,
                            status = ticket.status,
                            priority = ticket.priority,
                            category = ticket.category,
                            createdAt = ticket.createdAt,
                            updatedAt = ticket.updatedAt,
                            tags = ticket.tags,
                            resolution = ticket.resolution
                        )
                    )
                }
            }

            post("/get_user_tickets") {
                val body = call.receiveText()
                val json = Json.parseToJsonElement(body).jsonObject
                val userId = json["userId"]?.jsonPrimitive?.content ?: ""

                val user = supportData.users.firstOrNull {
                    it.id.equals(userId, ignoreCase = true) ||
                            it.email.equals(userId, ignoreCase = true)
                }

                if (user == null) {
                    call.respond(HttpStatusCode.NotFound, mapOf("error" to "user not found"))
                } else {
                    val userTickets = supportData.tickets
                        .filter { it.userId == user.id }
                        .sortedByDescending { it.updatedAt }
                        .map {
                            UserTicketResponse(
                                id = it.id,
                                subject = it.subject,
                                description = it.description,
                                status = it.status,
                                priority = it.priority,
                                category = it.category,
                                createdAt = it.createdAt,
                                updatedAt = it.updatedAt,
                                tags = it.tags
                            )
                        }
                    call.respond(userTickets)
                }
            }
        }
    }
}