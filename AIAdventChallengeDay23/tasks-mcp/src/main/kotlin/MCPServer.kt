package ru.iandreyshev

import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.types.*
import kotlinx.serialization.json.*
import java.io.BufferedReader
import java.io.InputStreamReader

data class User(
    val id: String,
    val email: String,
    val name: String,
    val role: String,
    val team: String
)

data class Project(
    val id: String,
    val name: String,
    val description: String
)

data class Task(
    val id: String,
    val projectId: String,
    val title: String,
    val description: String,
    val status: String,
    val priority: String,
    val assigneeId: String,
    val createdBy: String,
    val createdAt: String,
    val updatedAt: String,
    val dueDate: String?,
    val tags: List<String>,
    val estimatedHours: Int?,
    val blockedReason: String? = null
)

data class TaskData(
    val users: List<User>,
    val projects: List<Project>,
    val tasks: List<Task>
)

fun buildMcpServer(): Server {
    val taskData = loadTaskDataFromJson("/tasks.json")

    val server = Server(
        serverInfo = Implementation(
            name = "taskflow-mcp",
            version = "1.0.0",
            title = "TaskFlow Team Assistant MCP Server"
        ),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    // Tool: get_user_info
    // args:
    //   userId: string (required) - ID или email пользователя
    server.addTool(
        name = "get_user_info",
        description = "Получить информацию о члене команды по ID или email"
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val userIdOrEmail = argString(args, "userId").orEmpty()

        if (userIdOrEmail.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"userId is required"}"""))
            )
        }

        val user = taskData.users.firstOrNull {
            it.id.equals(userIdOrEmail, ignoreCase = true) ||
                    it.email.equals(userIdOrEmail, ignoreCase = true)
        } ?: return@addTool CallToolResult(
            content = listOf(TextContent("""{"error":"user not found","userId":"${escapeJson(userIdOrEmail)}"}"""))
        )

        val json = """{
          "id":"${escapeJson(user.id)}",
          "email":"${escapeJson(user.email)}",
          "name":"${escapeJson(user.name)}",
          "role":"${escapeJson(user.role)}",
          "team":"${escapeJson(user.team)}"
        }""".trimIndent()

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: get_task
    // args:
    //   taskId: string (required)
    server.addTool(
        name = "get_task",
        description = "Получить подробную информацию о задаче по ID"
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val taskId = argString(args, "taskId").orEmpty()

        if (taskId.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"taskId is required"}"""))
            )
        }

        val task = taskData.tasks.firstOrNull {
            it.id.equals(taskId, ignoreCase = true)
        } ?: return@addTool CallToolResult(
            content = listOf(TextContent("""{"error":"task not found","taskId":"${escapeJson(taskId)}"}"""))
        )

        val assignee = taskData.users.firstOrNull { it.id == task.assigneeId }
        val creator = taskData.users.firstOrNull { it.id == task.createdBy }
        val project = taskData.projects.firstOrNull { it.id == task.projectId }

        val json = """{
          "id":"${escapeJson(task.id)}",
          "projectId":"${escapeJson(task.projectId)}",
          "projectName":"${escapeJson(project?.name ?: "unknown")}",
          "title":"${escapeJson(task.title)}",
          "description":"${escapeJson(task.description)}",
          "status":"${escapeJson(task.status)}",
          "priority":"${escapeJson(task.priority)}",
          "assigneeId":"${escapeJson(task.assigneeId)}",
          "assigneeName":"${escapeJson(assignee?.name ?: "unknown")}",
          "assigneeEmail":"${escapeJson(assignee?.email ?: "unknown")}",
          "createdBy":"${escapeJson(task.createdBy)}",
          "createdByName":"${escapeJson(creator?.name ?: "unknown")}",
          "createdAt":"${escapeJson(task.createdAt)}",
          "updatedAt":"${escapeJson(task.updatedAt)}",
          "dueDate":${if (task.dueDate != null) """"${escapeJson(task.dueDate)}"""" else "null"},
          "tags":[${task.tags.joinToString(",") { """"${escapeJson(it)}"""" }}],
          "estimatedHours":${task.estimatedHours ?: "null"},
          "blockedReason":${if (task.blockedReason != null) """"${escapeJson(task.blockedReason)}"""" else "null"}
        }""".trimIndent()

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: search_tasks
    // args:
    //   projectId: string (optional) - фильтр по проекту
    //   assigneeId: string (optional) - фильтр по исполнителю
    //   status: string (optional) - todo, in_progress, done, blocked
    //   priority: string (optional) - low, medium, high, urgent
    server.addTool(
        name = "search_tasks",
        description = "Поиск задач по различным фильтрам (projectId, assigneeId, status, priority). Возвращает список задач отсортированный по приоритету и дате обновления."
    ) { request ->
        val args = request.arguments ?: emptyMap()

        val projectId = argString(args, "projectId")
        val assigneeId = argString(args, "assigneeId")
        val status = argString(args, "status")
        val priority = argString(args, "priority")

        val filtered = taskData.tasks.asSequence()
            .filter { projectId == null || it.projectId.equals(projectId, ignoreCase = true) }
            .filter { assigneeId == null || it.assigneeId.equals(assigneeId, ignoreCase = true) }
            .filter { status == null || it.status.equals(status, ignoreCase = true) }
            .filter { priority == null || it.priority.equals(priority, ignoreCase = true) }
            .sortedWith(
                compareByDescending<Task> { it.priority == "high" || it.priority == "urgent" }
                    .thenByDescending { it.updatedAt }
            )
            .toList()

        val json = buildJsonArray(filtered.map { t ->
            val assignee = taskData.users.firstOrNull { it.id == t.assigneeId }
            val project = taskData.projects.firstOrNull { it.id == t.projectId }
            """{
              "id":"${escapeJson(t.id)}",
              "projectId":"${escapeJson(t.projectId)}",
              "projectName":"${escapeJson(project?.name ?: "unknown")}",
              "title":"${escapeJson(t.title)}",
              "status":"${escapeJson(t.status)}",
              "priority":"${escapeJson(t.priority)}",
              "assigneeId":"${escapeJson(t.assigneeId)}",
              "assigneeName":"${escapeJson(assignee?.name ?: "unknown")}",
              "createdAt":"${escapeJson(t.createdAt)}",
              "updatedAt":"${escapeJson(t.updatedAt)}",
              "dueDate":${if (t.dueDate != null) """"${escapeJson(t.dueDate)}"""" else "null"}
            }""".trimIndent()
        })

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: get_user_tasks
    // args:
    //   userId: string (required) - ID или email пользователя
    server.addTool(
        name = "get_user_tasks",
        description = "Получить все задачи, назначенные конкретному пользователю"
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val userId = argString(args, "userId").orEmpty()

        if (userId.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"userId is required"}"""))
            )
        }

        val user = taskData.users.firstOrNull {
            it.id.equals(userId, ignoreCase = true) ||
                    it.email.equals(userId, ignoreCase = true)
        }

        if (user == null) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"user not found","userId":"${escapeJson(userId)}"}"""))
            )
        }

        val userTasks = taskData.tasks
            .filter { it.assigneeId == user.id }
            .sortedWith(
                compareByDescending<Task> { it.priority == "high" || it.priority == "urgent" }
                    .thenByDescending { it.updatedAt }
            )

        val json = buildJsonArray(userTasks.map { t ->
            val project = taskData.projects.firstOrNull { it.id == t.projectId }
            """{
              "id":"${escapeJson(t.id)}",
              "projectId":"${escapeJson(t.projectId)}",
              "projectName":"${escapeJson(project?.name ?: "unknown")}",
              "title":"${escapeJson(t.title)}",
              "description":"${escapeJson(t.description)}",
              "status":"${escapeJson(t.status)}",
              "priority":"${escapeJson(t.priority)}",
              "createdAt":"${escapeJson(t.createdAt)}",
              "updatedAt":"${escapeJson(t.updatedAt)}",
              "dueDate":${if (t.dueDate != null) """"${escapeJson(t.dueDate)}"""" else "null"},
              "tags":[${t.tags.joinToString(",") { """"${escapeJson(it)}"""" }}]
            }""".trimIndent()
        })

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: create_task
    // args:
    //   projectId: string (required) - ID проекта
    //   title: string (required) - название задачи
    //   description: string (required) - описание задачи
    //   priority: string (required) - low, medium, high, urgent
    //   assigneeId: string (required) - ID исполнителя
    //   createdBy: string (required) - ID создателя
    //   dueDate: string (optional) - срок выполнения в формате ISO
    //   tags: string (optional) - теги через запятую
    //   estimatedHours: number (optional) - оценка в часах
    server.addTool(
        name = "create_task",
        description = "Создать новую задачу в проекте"
    ) { request ->
        val args = request.arguments ?: emptyMap()

        val projectId = argString(args, "projectId").orEmpty()
        val title = argString(args, "title").orEmpty()
        val description = argString(args, "description").orEmpty()
        val priority = argString(args, "priority").orEmpty()
        val assigneeId = argString(args, "assigneeId").orEmpty()
        val createdBy = argString(args, "createdBy").orEmpty()
        val dueDate = argString(args, "dueDate")
        val tagsStr = argString(args, "tags")
        val estimatedHours = argString(args, "estimatedHours")?.toIntOrNull()

        // Валидация обязательных полей
        if (projectId.isBlank() || title.isBlank() || description.isBlank() ||
            priority.isBlank() || assigneeId.isBlank() || createdBy.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"required fields: projectId, title, description, priority, assigneeId, createdBy"}"""))
            )
        }

        // Проверяем существование проекта
        val project = taskData.projects.firstOrNull { it.id == projectId }
        if (project == null) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"project not found","projectId":"${escapeJson(projectId)}"}"""))
            )
        }

        // Проверяем существование исполнителя
        val assignee = taskData.users.firstOrNull { it.id == assigneeId }
        if (assignee == null) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"assignee not found","assigneeId":"${escapeJson(assigneeId)}"}"""))
            )
        }

        // Проверяем существование создателя
        val creator = taskData.users.firstOrNull { it.id == createdBy }
        if (creator == null) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"creator not found","createdBy":"${escapeJson(createdBy)}"}"""))
            )
        }

        // Генерируем ID для новой задачи
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

        // Добавляем задачу в список (в реальной системе это была бы запись в БД)
        (taskData.tasks as MutableList).add(newTask)

        val json = """{
          "success":true,
          "task":{
            "id":"${escapeJson(newTask.id)}",
            "projectId":"${escapeJson(newTask.projectId)}",
            "projectName":"${escapeJson(project.name)}",
            "title":"${escapeJson(newTask.title)}",
            "description":"${escapeJson(newTask.description)}",
            "status":"${escapeJson(newTask.status)}",
            "priority":"${escapeJson(newTask.priority)}",
            "assigneeId":"${escapeJson(newTask.assigneeId)}",
            "assigneeName":"${escapeJson(assignee.name)}",
            "createdBy":"${escapeJson(newTask.createdBy)}",
            "createdByName":"${escapeJson(creator.name)}",
            "createdAt":"${escapeJson(newTask.createdAt)}",
            "updatedAt":"${escapeJson(newTask.updatedAt)}",
            "dueDate":${if (newTask.dueDate != null) """"${escapeJson(newTask.dueDate)}"""" else "null"},
            "tags":[${newTask.tags.joinToString(",") { """"${escapeJson(it)}"""" }}],
            "estimatedHours":${newTask.estimatedHours ?: "null"}
          }
        }""".trimIndent()

        CallToolResult(content = listOf(TextContent(json)))
    }

    return server
}

fun loadTaskDataFromJson(resourcePath: String): TaskData {
    val stream = object {}.javaClass.getResourceAsStream(resourcePath)
        ?: throw IllegalStateException("Resource not found: $resourcePath (put it in src/main/resources)")

    val jsonText = BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).use { it.readText() }
    val jsonElement = Json.parseToJsonElement(jsonText).jsonObject

    val users = jsonElement["users"]?.jsonArray?.map { userElement ->
        val obj = userElement.jsonObject
        User(
            id = obj["id"]?.jsonPrimitive?.content ?: "",
            email = obj["email"]?.jsonPrimitive?.content ?: "",
            name = obj["name"]?.jsonPrimitive?.content ?: "",
            role = obj["role"]?.jsonPrimitive?.content ?: "",
            team = obj["team"]?.jsonPrimitive?.content ?: ""
        )
    } ?: emptyList()

    val projects = jsonElement["projects"]?.jsonArray?.map { projectElement ->
        val obj = projectElement.jsonObject
        Project(
            id = obj["id"]?.jsonPrimitive?.content ?: "",
            name = obj["name"]?.jsonPrimitive?.content ?: "",
            description = obj["description"]?.jsonPrimitive?.content ?: ""
        )
    } ?: emptyList()

    val tasks = jsonElement["tasks"]?.jsonArray?.map { taskElement ->
        val obj = taskElement.jsonObject
        Task(
            id = obj["id"]?.jsonPrimitive?.content ?: "",
            projectId = obj["projectId"]?.jsonPrimitive?.content ?: "",
            title = obj["title"]?.jsonPrimitive?.content ?: "",
            description = obj["description"]?.jsonPrimitive?.content ?: "",
            status = obj["status"]?.jsonPrimitive?.content ?: "",
            priority = obj["priority"]?.jsonPrimitive?.content ?: "",
            assigneeId = obj["assigneeId"]?.jsonPrimitive?.content ?: "",
            createdBy = obj["createdBy"]?.jsonPrimitive?.content ?: "",
            createdAt = obj["createdAt"]?.jsonPrimitive?.content ?: "",
            updatedAt = obj["updatedAt"]?.jsonPrimitive?.content ?: "",
            dueDate = obj["dueDate"]?.jsonPrimitive?.content,
            tags = obj["tags"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList(),
            estimatedHours = obj["estimatedHours"]?.jsonPrimitive?.content?.toIntOrNull(),
            blockedReason = obj["blockedReason"]?.jsonPrimitive?.content
        )
    }?.toMutableList() ?: mutableListOf()

    return TaskData(users, projects, tasks)
}

private fun buildJsonArray(items: List<String>): String =
    "[${items.joinToString(",")}]"

private fun escapeJson(s: String): String =
    s.replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")

private fun argString(args: Map<String, Any?>, key: String): String? {
    val v = args[key] ?: return null
    val s = when (v) {
        is String -> v
        is JsonPrimitive -> v.content
        else -> v.toString()
    }.trim()
    return s.removeSurrounding("\"").trim()
}
