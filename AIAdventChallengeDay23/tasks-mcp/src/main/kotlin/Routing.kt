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
    val role: String,
    val team: String
)

@Serializable
data class TaskResponse(
    val id: String,
    val projectId: String,
    val projectName: String,
    val title: String,
    val description: String,
    val status: String,
    val priority: String,
    val assigneeId: String,
    val assigneeName: String,
    val assigneeEmail: String,
    val createdBy: String,
    val createdByName: String,
    val createdAt: String,
    val updatedAt: String,
    val dueDate: String?,
    val tags: List<String>,
    val estimatedHours: Int?,
    val blockedReason: String?
)

@Serializable
data class UserTaskResponse(
    val id: String,
    val projectId: String,
    val projectName: String,
    val title: String,
    val description: String,
    val status: String,
    val priority: String,
    val createdAt: String,
    val updatedAt: String,
    val dueDate: String?,
    val tags: List<String>
)

@Serializable
data class CreateTaskRequest(
    val projectId: String,
    val title: String,
    val description: String,
    val priority: String,
    val assigneeId: String,
    val createdBy: String,
    val dueDate: String? = null,
    val tags: String? = null,
    val estimatedHours: Int? = null
)

fun Application.configureRouting() {
    install(io.ktor.server.sse.SSE)
    install(io.ktor.server.plugins.contentnegotiation.ContentNegotiation) {
        json()
    }

    val taskData = loadTaskDataFromJson("/tasks.json")

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

                val user = taskData.users.firstOrNull {
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
                            role = user.role,
                            team = user.team
                        )
                    )
                }
            }

            post("/get_task") {
                val body = call.receiveText()
                val json = Json.parseToJsonElement(body).jsonObject
                val taskId = json["taskId"]?.jsonPrimitive?.content ?: ""

                val task = taskData.tasks.firstOrNull {
                    it.id.equals(taskId, ignoreCase = true)
                }

                if (task == null) {
                    call.respond(HttpStatusCode.NotFound, mapOf("error" to "task not found"))
                } else {
                    val assignee = taskData.users.firstOrNull { it.id == task.assigneeId }
                    val creator = taskData.users.firstOrNull { it.id == task.createdBy }
                    val project = taskData.projects.firstOrNull { it.id == task.projectId }

                    call.respond(
                        TaskResponse(
                            id = task.id,
                            projectId = task.projectId,
                            projectName = project?.name ?: "unknown",
                            title = task.title,
                            description = task.description,
                            status = task.status,
                            priority = task.priority,
                            assigneeId = task.assigneeId,
                            assigneeName = assignee?.name ?: "unknown",
                            assigneeEmail = assignee?.email ?: "unknown",
                            createdBy = task.createdBy,
                            createdByName = creator?.name ?: "unknown",
                            createdAt = task.createdAt,
                            updatedAt = task.updatedAt,
                            dueDate = task.dueDate,
                            tags = task.tags,
                            estimatedHours = task.estimatedHours,
                            blockedReason = task.blockedReason
                        )
                    )
                }
            }

            post("/get_user_tasks") {
                val body = call.receiveText()
                val json = Json.parseToJsonElement(body).jsonObject
                val userId = json["userId"]?.jsonPrimitive?.content ?: ""

                val user = taskData.users.firstOrNull {
                    it.id.equals(userId, ignoreCase = true) ||
                            it.email.equals(userId, ignoreCase = true)
                }

                if (user == null) {
                    call.respond(HttpStatusCode.NotFound, mapOf("error" to "user not found"))
                } else {
                    val userTasks = taskData.tasks
                        .filter { it.assigneeId == user.id }
                        .sortedWith(
                            compareByDescending<Task> { it.priority == "high" || it.priority == "urgent" }
                                .thenByDescending { it.updatedAt }
                        )
                        .map {
                            val project = taskData.projects.firstOrNull { p -> p.id == it.projectId }
                            UserTaskResponse(
                                id = it.id,
                                projectId = it.projectId,
                                projectName = project?.name ?: "unknown",
                                title = it.title,
                                description = it.description,
                                status = it.status,
                                priority = it.priority,
                                createdAt = it.createdAt,
                                updatedAt = it.updatedAt,
                                dueDate = it.dueDate,
                                tags = it.tags
                            )
                        }
                    call.respond(userTasks)
                }
            }

            post("/search_tasks") {
                val body = call.receiveText()
                val json = Json.parseToJsonElement(body).jsonObject

                val projectId = json["projectId"]?.jsonPrimitive?.content
                val assigneeId = json["assigneeId"]?.jsonPrimitive?.content
                val status = json["status"]?.jsonPrimitive?.content
                val priority = json["priority"]?.jsonPrimitive?.content

                val filtered = taskData.tasks.asSequence()
                    .filter { projectId == null || it.projectId.equals(projectId, ignoreCase = true) }
                    .filter { assigneeId == null || it.assigneeId.equals(assigneeId, ignoreCase = true) }
                    .filter { status == null || it.status.equals(status, ignoreCase = true) }
                    .filter { priority == null || it.priority.equals(priority, ignoreCase = true) }
                    .sortedWith(
                        compareByDescending<Task> { it.priority == "high" || it.priority == "urgent" }
                            .thenByDescending { it.updatedAt }
                    )
                    .map {
                        val project = taskData.projects.firstOrNull { p -> p.id == it.projectId }
                        val assignee = taskData.users.firstOrNull { u -> u.id == it.assigneeId }
                        UserTaskResponse(
                            id = it.id,
                            projectId = it.projectId,
                            projectName = project?.name ?: "unknown",
                            title = it.title,
                            description = it.description,
                            status = it.status,
                            priority = it.priority,
                            createdAt = it.createdAt,
                            updatedAt = it.updatedAt,
                            dueDate = it.dueDate,
                            tags = it.tags
                        )
                    }
                    .toList()

                call.respond(filtered)
            }

            post("/create_task") {
                val body = call.receiveText()
                val json = Json.parseToJsonElement(body).jsonObject

                val projectId = json["projectId"]?.jsonPrimitive?.content ?: ""
                val title = json["title"]?.jsonPrimitive?.content ?: ""
                val description = json["description"]?.jsonPrimitive?.content ?: ""
                val priority = json["priority"]?.jsonPrimitive?.content ?: ""
                val assigneeId = json["assigneeId"]?.jsonPrimitive?.content ?: ""
                val createdBy = json["createdBy"]?.jsonPrimitive?.content ?: ""
                val dueDate = json["dueDate"]?.jsonPrimitive?.content
                val tagsStr = json["tags"]?.jsonPrimitive?.content
                val estimatedHours = json["estimatedHours"]?.jsonPrimitive?.content?.toIntOrNull()

                if (projectId.isBlank() || title.isBlank() || description.isBlank() ||
                    priority.isBlank() || assigneeId.isBlank() || createdBy.isBlank()) {
                    call.respond(HttpStatusCode.BadRequest, mapOf("error" to "required fields missing"))
                    return@post
                }

                val project = taskData.projects.firstOrNull { it.id == projectId }
                if (project == null) {
                    call.respond(HttpStatusCode.NotFound, mapOf("error" to "project not found"))
                    return@post
                }

                val assignee = taskData.users.firstOrNull { it.id == assigneeId }
                if (assignee == null) {
                    call.respond(HttpStatusCode.NotFound, mapOf("error" to "assignee not found"))
                    return@post
                }

                val creator = taskData.users.firstOrNull { it.id == createdBy }
                if (creator == null) {
                    call.respond(HttpStatusCode.NotFound, mapOf("error" to "creator not found"))
                    return@post
                }

                val newTaskId = "task${(taskData.tasks.size + 1).toString().padStart(3, '0')}"
                val now = java.time.Instant.now().toString()
                val tags = tagsStr?.split(",")?.map { it.trim() } ?: emptyList()

                val newTask = Task(
                    id = newTaskId,
                    projectId = projectId,
                    title = title,
                    description = description,
                    status = "todo",
                    priority = priority,
                    assigneeId = assigneeId,
                    createdBy = createdBy,
                    createdAt = now,
                    updatedAt = now,
                    dueDate = dueDate,
                    tags = tags,
                    estimatedHours = estimatedHours
                )

                (taskData.tasks as MutableList).add(newTask)

                call.respond(
                    HttpStatusCode.Created,
                    TaskResponse(
                        id = newTask.id,
                        projectId = newTask.projectId,
                        projectName = project.name,
                        title = newTask.title,
                        description = newTask.description,
                        status = newTask.status,
                        priority = newTask.priority,
                        assigneeId = newTask.assigneeId,
                        assigneeName = assignee.name,
                        assigneeEmail = assignee.email,
                        createdBy = newTask.createdBy,
                        createdByName = creator.name,
                        createdAt = newTask.createdAt,
                        updatedAt = newTask.updatedAt,
                        dueDate = newTask.dueDate,
                        tags = newTask.tags,
                        estimatedHours = newTask.estimatedHours,
                        blockedReason = null
                    )
                )
            }
        }
    }
}