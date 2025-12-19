package ru.iandreyshev

import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.types.*
import kotlinx.serialization.json.JsonPrimitive
import java.time.LocalTime
import java.time.format.DateTimeParseException
import kotlin.math.roundToInt

data class Attraction(
    val id: String,
    val city: String,
    val name: String,
    val category: String,   // "еда" | "музей" | "природа" | "прогулка" | "вид" | "развлечения"
    val area: String,
    val metroOrPoint: String,
    val openFrom: String,   // HH:mm
    val openTo: String,     // HH:mm
    val avgTimeMin: Int,
    val priceRub: Int,
    val highlight: String
)

data class DayPlan(
    val day: Int,
    val title: String,
    val items: List<String>
)

fun buildMcpServer(): Server {
    val attractions = loadAttractionsFromJson("/attractions.json")

    val server = Server(
        serverInfo = Implementation(
            name = "itinerary-mcp",
            version = "1.0.0",
            title = "Itinerary MCP Server (Russia, local JSON)"
        ),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    // Tool: get_attractions
    // args:
    //   city (required)
    //   category (optional)
    //   openNow (optional, "true"/"false") -> uses server local time
    //   maxPriceRub (optional)
    server.addTool(
        name = "get_attractions",
        description = "Вернуть достопримечательности/места в городе РФ (тестовый JSON). Фильтры: category, openNow, maxPriceRub."
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val city = argString(args, "city").orEmpty()
        if (city.isBlank()) {
            return@addTool CallToolResult(content = listOf(TextContent("""{"error":"city is required"}""")))
        }
        val category = argString(args, "category")?.lowercase()
        val openNow = (argString(args, "openNow") ?: "false").lowercase() == "true"
        val maxPrice = argInt(args, "maxPriceRub")

        val now = LocalTime.now()
        val filtered = attractions.asSequence()
            .filter { it.city.equals(city, ignoreCase = true) }
            .filter { category.isNullOrBlank() || it.category.lowercase() == category }
            .filter { maxPrice == null || it.priceRub <= maxPrice }
            .filter {
                if (!openNow) true
                else isOpenNow(it.openFrom, it.openTo, now)
            }
            .sortedWith(compareBy<Attraction> { it.priceRub }.thenByDescending { it.avgTimeMin })
            .toList()

        val json = buildJsonArray(filtered.map { a ->
            """{
              "id":"${escapeJson(a.id)}",
              "city":"${escapeJson(a.city)}",
              "name":"${escapeJson(a.name)}",
              "category":"${escapeJson(a.category)}",
              "area":"${escapeJson(a.area)}",
              "metroOrPoint":"${escapeJson(a.metroOrPoint)}",
              "openFrom":"${escapeJson(a.openFrom)}",
              "openTo":"${escapeJson(a.openTo)}",
              "avgTimeMin":${a.avgTimeMin},
              "priceRub":${a.priceRub},
              "highlight":"${escapeJson(a.highlight)}"
            }""".trimIndent()
        })

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: build_3day_itinerary
    // args:
    //   city (required)
    //   pace (optional: "slow"|"normal"|"fast") default normal
    //   budget (optional: "econom"|"mid"|"premium") default mid
    server.addTool(
        name = "build_3day_itinerary",
        description = "Собрать маршрут на 3 дня по городу на базе тестовых мест. Аргументы: city, pace(slow|normal|fast), budget(econom|mid|premium)."
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val city = argString(args, "city").orEmpty()
        if (city.isBlank()) {
            return@addTool CallToolResult(content = listOf(TextContent("""{"error":"city is required"}""")))
        }

        val pace = (argString(args, "pace") ?: "normal").lowercase()
        val budget = (argString(args, "budget") ?: "mid").lowercase()

        val cityPlaces = attractions.filter { it.city.equals(city, ignoreCase = true) }
        if (cityPlaces.isEmpty()) {
            return@addTool CallToolResult(content = listOf(TextContent("""{"error":"no data for city","city":"${escapeJson(city)}"}""")))
        }

        val maxItemsPerDay = when (pace) {
            "slow" -> 3
            "fast" -> 6
            else -> 4
        }

        val priceCap = when (budget) {
            "econom" -> 700
            "premium" -> 10_000
            else -> 3000
        }

        val picks = cityPlaces
            .filter { it.priceRub <= priceCap }
            .sortedWith(
                compareBy<Attraction> { categoryRank(it.category) }
                    .thenByDescending { it.avgTimeMin }
                    .thenBy { it.priceRub }
            )

        // Жадно раскладываем по дням: микс категорий
        val days = mutableListOf(
            mutableListOf<Attraction>(),
            mutableListOf(),
            mutableListOf()
        )

        for (a in picks) {
            val bestDayIndex = days.indices.minBy { days[it].size }
            if (days[bestDayIndex].size < maxItemsPerDay) {
                // избегаем повторов категории подряд внутри одного дня
                val last = days[bestDayIndex].lastOrNull()
                if (last == null || last.category != a.category || days[bestDayIndex].size < 2) {
                    days[bestDayIndex].add(a)
                }
            }
            if (days.all { it.size >= maxItemsPerDay }) break
        }

        // Если вдруг где-то пусто — добьём самыми дешёвыми
        for (i in 0..2) {
            if (days[i].isEmpty()) {
                days[i].addAll(picks.take(maxItemsPerDay))
            }
        }

        val dayPlans = days.mapIndexed { idx, list ->
            val dayNum = idx + 1
            val title = when (dayNum) {
                1 -> "Знакомство и прогулки"
                2 -> "Культура и виды"
                else -> "Еда, сувениры и расслабление"
            }
            val items = list.map { a ->
                "${a.name} — ${a.category}, ${a.area} (${a.metroOrPoint}), ${a.openFrom}-${a.openTo}, ~${a.avgTimeMin} мин, ${a.priceRub}₽. ${a.highlight}"
            }
            DayPlan(day = dayNum, title = title, items = items)
        }

        val totalTime = dayPlans.sumOf { dp -> dp.items.size } // грубо, для демо
        val avgSpend = days.flatten().sumOf { it.priceRub }

        val json = """{
          "city":"${escapeJson(city)}",
          "pace":"${escapeJson(pace)}",
          "budget":"${escapeJson(budget)}",
          "summary":{
            "days":3,
            "placesPlanned":$totalTime,
            "estimatedTicketsRub":$avgSpend,
            "notes":"Оценка примерная: это тестовый маршрут, время/стоимость округлены."
          },
          "plan":[
            ${dayPlans.joinToString(",") { dp ->
            """{
                  "day":${dp.day},
                  "title":"${escapeJson(dp.title)}",
                  "items":[${dp.items.joinToString(",") { """"${escapeJson(it)}"""" }}]
                }""".trimIndent()
        }}
          ]
        }""".trimIndent()

        CallToolResult(content = listOf(TextContent(json)))
    }

    return server
}

private fun categoryRank(category: String): Int {
    // чтобы в маршруте был микс: прогулка/вид/музей/еда/природа/развлечения
    return when (category.lowercase()) {
        "прогулка" -> 1
        "вид" -> 2
        "музей" -> 3
        "природа" -> 4
        "еда" -> 5
        "развлечения" -> 6
        else -> 10
    }
}

private fun isOpenNow(openFrom: String, openTo: String, now: LocalTime): Boolean {
    val from = tryParseTime(openFrom) ?: return false
    val to = tryParseTime(openTo) ?: return false
    // простой случай: same-day интервал
    if (to.isAfter(from)) return !now.isBefore(from) && now.isBefore(to)
    // если вдруг через полночь (редко тут)
    return !now.isBefore(from) || now.isBefore(to)
}

private fun tryParseTime(s: String): LocalTime? =
    try { LocalTime.parse(s.trim()) } catch (_: DateTimeParseException) { null }

// ----- Minimal JSON loader for our file -----

private fun loadAttractionsFromJson(resourcePath: String): List<Attraction> {
    val stream = object {}.javaClass.getResourceAsStream(resourcePath)
        ?: throw IllegalStateException("Resource not found: $resourcePath (put it in src/main/resources)")
    val json = stream.bufferedReader(Charsets.UTF_8).readText()

    // Expected:
    // { "attractions": [ { ... }, { ... } ] }
    val block = Regex("\"attractions\"\\s*:\\s*\\[(.*)]", RegexOption.DOT_MATCHES_ALL)
        .find(json)?.groupValues?.get(1) ?: return emptyList()

    val objRegex = Regex("\\{(.*?)\\}", RegexOption.DOT_MATCHES_ALL)
    return objRegex.findAll(block).map { m ->
        val obj = m.groupValues[1]
        fun str(key: String): String =
            Regex("\"$key\"\\s*:\\s*\"(.*?)\"", RegexOption.DOT_MATCHES_ALL).find(obj)?.groupValues?.get(1) ?: ""
        fun int(key: String): Int =
            Regex("\"$key\"\\s*:\\s*(\\d+)").find(obj)?.groupValues?.get(1)?.toInt() ?: 0

        Attraction(
            id = str("id"),
            city = str("city"),
            name = str("name"),
            category = str("category"),
            area = str("area"),
            metroOrPoint = str("metroOrPoint"),
            openFrom = str("openFrom"),
            openTo = str("openTo"),
            avgTimeMin = int("avgTimeMin"),
            priceRub = int("priceRub"),
            highlight = str("highlight")
        )
    }.toList()
}

// ----- JSON helpers -----

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

private fun argInt(args: Map<String, Any?>, key: String): Int? =
    argString(args, key)?.toIntOrNull()

private fun argDouble(args: Map<String, Any?>, key: String): Double? =
    argString(args, key)?.toDoubleOrNull()