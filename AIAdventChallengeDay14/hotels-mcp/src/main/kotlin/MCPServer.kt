package ru.iandreyshev

import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.types.*
import kotlinx.serialization.json.JsonPrimitive
import java.io.BufferedReader
import java.io.InputStreamReader
import java.time.LocalDate
import java.time.format.DateTimeParseException
import kotlin.math.roundToInt

data class Hotel(
    val id: String,
    val city: String,
    val name: String,
    val stars: Int,
    val pricePerNightRub: Int,
    val rating: Double,
    val area: String,
    val nearMetro: String,
    val features: List<String>
)

fun buildMcpServer(): Server {
    val hotels = loadHotelsFromCsv("/hotels.csv")

    val server = Server(
        serverInfo = Implementation(
            name = "hotels-mcp",
            version = "1.0.0",
            title = "Hotels MCP Server (Russia, local CSV)"
        ),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    // Tool: search_hotels
    // args:
    //   city: string (required)
    //   fromDate: string YYYY-MM-DD (optional)
    //   toDate: string YYYY-MM-DD (optional)
    //   maxPriceRub: string/int (optional)
    //   stars: string/int (optional)
    //   nearMetro: string (optional, exact match, e.g. "Пушкинская")
    server.addTool(
        name = "search_hotels",
        description = "Найти отели в городе РФ по тестовым данным (CSV). Фильтры: maxPriceRub, stars, nearMetro."
    ) { request ->
        val args = request.arguments ?: emptyMap()

        val city = argString(args, "city").orEmpty()
        if (city.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"city is required"}"""))
            )
        }

        val maxPrice = argInt(args, "maxPriceRub")
        val stars = argInt(args, "stars")
        val nearMetro = argString(args, "nearMetro")

        // Даты сейчас не влияют на доступность (тестовый сервер),
        // но мы их валидируем, чтобы агент видел "реалистичность".
        val fromDateRaw = argString(args, "fromDate")
        val toDateRaw = argString(args, "toDate")
        val dateValidation = validateDates(fromDateRaw, toDateRaw)
        if (dateValidation != null) {
            return@addTool CallToolResult(
                content = listOf(TextContent(dateValidation))
            )
        }

        val filtered = hotels.asSequence()
            .filter { it.city.equals(city, ignoreCase = true) }
            .filter { maxPrice == null || it.pricePerNightRub <= maxPrice }
            .filter { stars == null || it.stars == stars }
            .filter { nearMetro.isNullOrBlank() || it.nearMetro.equals(nearMetro, ignoreCase = true) }
            .sortedWith(compareBy<Hotel> { it.pricePerNightRub }.thenByDescending { it.rating })
            .toList()

        val json = buildJsonArray(filtered.map { h ->
            """{
              "id":"${escapeJson(h.id)}",
              "city":"${escapeJson(h.city)}",
              "name":"${escapeJson(h.name)}",
              "stars":${h.stars},
              "pricePerNightRub":${h.pricePerNightRub},
              "rating":${((h.rating * 10.0).roundToInt() / 10.0)},
              "area":"${escapeJson(h.area)}",
              "nearMetro":"${escapeJson(h.nearMetro)}",
              "features":[${h.features.joinToString(",") { """"${escapeJson(it)}"""" }}]
            }""".trimIndent()
        })

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: get_hotel_details
    // args:
    //   hotelId: string (required)
    server.addTool(
        name = "get_hotel_details",
        description = "Получить подробности отеля по hotelId (из тестового CSV)."
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val hotelId = argString(args, "hotelId").orEmpty()

        if (hotelId.isBlank()) {
            return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"hotelId is required"}"""))
            )
        }

        val h = hotels.firstOrNull { it.id.equals(hotelId, ignoreCase = true) }
            ?: return@addTool CallToolResult(
                content = listOf(TextContent("""{"error":"hotel not found","hotelId":"${escapeJson(hotelId)}"}"""))
            )

        val json = """{
          "id":"${escapeJson(h.id)}",
          "city":"${escapeJson(h.city)}",
          "name":"${escapeJson(h.name)}",
          "stars":${h.stars},
          "pricePerNightRub":${h.pricePerNightRub},
          "rating":${((h.rating * 10.0).roundToInt() / 10.0)},
          "area":"${escapeJson(h.area)}",
          "nearMetro":"${escapeJson(h.nearMetro)}",
          "features":[${h.features.joinToString(",") { """"${escapeJson(it)}"""" }}],
          "policies":{
            "checkIn":"14:00",
            "checkOut":"12:00",
            "cancel":"Бесплатно за 24 часа (тестовые условия)"
          },
          "contact":{
            "phone":"+7 (000) 000-00-00",
            "email":"booking@${escapeJson(h.id.lowercase())}.example"
          }
        }""".trimIndent()

        CallToolResult(content = listOf(TextContent(json)))
    }

    return server
}

private fun validateDates(fromDateRaw: String?, toDateRaw: String?): String? {
    if (fromDateRaw.isNullOrBlank() && toDateRaw.isNullOrBlank()) return null

    val from = tryParseDate(fromDateRaw)
    val to = tryParseDate(toDateRaw)

    if (fromDateRaw != null && from == null) {
        return """{"error":"fromDate must be YYYY-MM-DD","fromDate":"${escapeJson(fromDateRaw)}"}"""
    }
    if (toDateRaw != null && to == null) {
        return """{"error":"toDate must be YYYY-MM-DD","toDate":"${escapeJson(toDateRaw)}"}"""
    }
    if (from != null && to != null && !to.isAfter(from)) {
        return """{"error":"toDate must be after fromDate","fromDate":"${escapeJson(fromDateRaw!!)}","toDate":"${escapeJson(toDateRaw!!)}"}"""
    }
    return null
}

private fun tryParseDate(s: String?): LocalDate? {
    if (s.isNullOrBlank()) return null
    return try {
        LocalDate.parse(s.trim())
    } catch (_: DateTimeParseException) {
        null
    }
}

private fun loadHotelsFromCsv(resourcePath: String): List<Hotel> {
    val stream = object {}.javaClass.getResourceAsStream(resourcePath)
        ?: throw IllegalStateException("Resource not found: $resourcePath (put it in src/main/resources)")

    BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).use { br ->
        val lines = br.lineSequence().toList()
        if (lines.isEmpty()) return emptyList()

        // header:
        // id,city,name,stars,pricePerNightRub,rating,area,nearMetro,features
        return lines.drop(1)
            .filter { it.isNotBlank() && !it.trim().startsWith("#") }
            .map { parseHotelCsvLine(it) }
    }
}

private fun parseHotelCsvLine(line: String): Hotel {
    // Простая CSV-парсилка: значения без запятых внутри (для тестовых данных хватает)
    val parts = line.split(",").map { it.trim() }
    require(parts.size >= 9) { "Bad CSV line (need 9 cols): $line" }

    val id = parts[0]
    val city = parts[1]
    val name = parts[2]
    val stars = parts[3].toInt()
    val price = parts[4].toInt()
    val rating = parts[5].toDouble()
    val area = parts[6]
    val nearMetro = parts[7]
    val features = parts[8].split(";").map { it.trim() }.filter { it.isNotEmpty() }

    return Hotel(
        id = id,
        city = city,
        name = name,
        stars = stars,
        pricePerNightRub = price,
        rating = rating,
        area = area,
        nearMetro = nearMetro,
        features = features
    )
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

private fun argInt(args: Map<String, Any?>, key: String): Int? =
    argString(args, key)?.toIntOrNull()

private fun argDouble(args: Map<String, Any?>, key: String): Double? =
    argString(args, key)?.toDoubleOrNull()