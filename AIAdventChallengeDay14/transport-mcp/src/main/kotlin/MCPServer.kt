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

data class TrainTrip(
    val id: String,
    val fromCity: String,
    val toCity: String,
    val date: String,        // YYYY-MM-DD
    val departTime: String,  // HH:mm
    val arriveTime: String,  // HH:mm
    val durationMin: Int,
    val train: String,
    val seatClass: String,
    val priceRub: Int,
    val seatsLeft: Int
)

data class FlightTrip(
    val id: String,
    val fromCity: String,
    val toCity: String,
    val date: String,        // YYYY-MM-DD
    val departTime: String,  // HH:mm
    val arriveTime: String,  // HH:mm
    val durationMin: Int,
    val airline: String,
    val priceRub: Int,
    val baggage: String
)

data class TaxiRule(
    val city: String,
    val baseRub: Int,
    val perKmRub: Int,
    val surge: Double,
    val notes: String
)

fun buildMcpServer(): Server {
    val trains = loadTrainsFromCsv("/trains.csv")
    val flights = loadFlightsFromCsv("/flights.csv")
    val taxiRules = loadTaxiRulesFromJson("/taxi_rules.json")

    val server = Server(
        serverInfo = Implementation(
            name = "transport-mcp",
            version = "1.0.0",
            title = "Transport MCP Server (Russia, local CSV/JSON)"
        ),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    // Tool: search_trains
    // args: fromCity (req), toCity (req), date YYYY-MM-DD (req)
    server.addTool(
        name = "search_trains",
        description = "Найти поезда по РФ (тестовые данные). Аргументы: fromCity, toCity, date(YYYY-MM-DD)."
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val from = args["fromCity"]?.toString()?.trim().orEmpty()
        val to = args["toCity"]?.toString()?.trim().orEmpty()
        val date = args["date"]?.toString()?.trim().orEmpty()

        val err = validateRouteAndDate(from, to, date)
        if (err != null) return@addTool CallToolResult(content = listOf(TextContent(err)))

        val results = trains.asSequence()
            .filter { it.fromCity.equals(from, ignoreCase = true) }
            .filter { it.toCity.equals(to, ignoreCase = true) }
            .filter { it.date == date }
            .sortedWith(compareBy<TrainTrip> { it.priceRub }.thenByDescending { it.seatsLeft })
            .toList()

        val json = buildJsonArray(results.map { t ->
            """{
              "id":"${escapeJson(t.id)}",
              "type":"train",
              "fromCity":"${escapeJson(t.fromCity)}",
              "toCity":"${escapeJson(t.toCity)}",
              "date":"${escapeJson(t.date)}",
              "departTime":"${escapeJson(t.departTime)}",
              "arriveTime":"${escapeJson(t.arriveTime)}",
              "durationMin":${t.durationMin},
              "train":"${escapeJson(t.train)}",
              "seatClass":"${escapeJson(t.seatClass)}",
              "priceRub":${t.priceRub},
              "seatsLeft":${t.seatsLeft}
            }""".trimIndent()
        })

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: search_flights
    // args: fromCity (req), toCity (req), date YYYY-MM-DD (req)
    server.addTool(
        name = "search_flights",
        description = "Найти авиарейсы по РФ (тестовые данные). Аргументы: fromCity, toCity, date(YYYY-MM-DD)."
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val from = argString(args, "fromCity").orEmpty()
        val to = argString(args, "toCity").orEmpty()
        val date = argString(args, "date").orEmpty()

        val err = validateRouteAndDate(from, to, date)
        if (err != null) return@addTool CallToolResult(content = listOf(TextContent(err)))

        val results = flights.asSequence()
            .filter { it.fromCity.equals(from, ignoreCase = true) }
            .filter { it.toCity.equals(to, ignoreCase = true) }
            .filter { it.date == date }
            .sortedBy { it.priceRub }
            .toList()

        val json = buildJsonArray(results.map { f ->
            """{
              "id":"${escapeJson(f.id)}",
              "type":"flight",
              "fromCity":"${escapeJson(f.fromCity)}",
              "toCity":"${escapeJson(f.toCity)}",
              "date":"${escapeJson(f.date)}",
              "departTime":"${escapeJson(f.departTime)}",
              "arriveTime":"${escapeJson(f.arriveTime)}",
              "durationMin":${f.durationMin},
              "airline":"${escapeJson(f.airline)}",
              "baggage":"${escapeJson(f.baggage)}",
              "priceRub":${f.priceRub}
            }""".trimIndent()
        })

        CallToolResult(content = listOf(TextContent(json)))
    }

    // Tool: estimate_taxi
    // args: city(req), km(optional default 7), timeOfDay(optional: "day"|"night"), comfort(optional: "econom"|"comfort")
    server.addTool(
        name = "estimate_taxi",
        description = "Оценить стоимость такси в городе (тестовые правила). Аргументы: city, km(по умолч. 7), timeOfDay(day|night), comfort(econom|comfort)."
    ) { request ->
        val args = request.arguments ?: emptyMap()
        val city = argString(args, "city").orEmpty()
        if (city.isBlank()) {
            return@addTool CallToolResult(content = listOf(TextContent("""{"error":"city is required"}""")))
        }

        val km = argDouble(args, "km") ?: 7.0
        val timeOfDay = (argString(args, "timeOfDay") ?: "day").lowercase()
        val comfort = (argString(args, "comfort") ?: "econom").lowercase()

        val rule = taxiRules.firstOrNull { it.city.equals(city, ignoreCase = true) }
            ?: return@addTool CallToolResult(content = listOf(TextContent("""{"error":"unknown city for taxi","city":"${escapeJson(city)}"}""")))

        val nightMultiplier = if (timeOfDay == "night") 1.2 else 1.0
        val comfortMultiplier = if (comfort == "comfort") 1.25 else 1.0

        val raw = (rule.baseRub + (km * rule.perKmRub)) * rule.surge * nightMultiplier * comfortMultiplier
        val price = raw.roundToInt()

        val json = """{
          "city":"${escapeJson(city)}",
          "km":$km,
          "timeOfDay":"${escapeJson(timeOfDay)}",
          "comfort":"${escapeJson(comfort)}",
          "estimateRub":$price,
          "details":{
            "baseRub":${rule.baseRub},
            "perKmRub":${rule.perKmRub},
            "surge":${((rule.surge * 100.0).roundToInt() / 100.0)},
            "notes":"${escapeJson(rule.notes)}"
          }
        }""".trimIndent()

        CallToolResult(content = listOf(TextContent(json)))
    }

    return server
}

private fun validateRouteAndDate(from: String, to: String, date: String): String? {
    if (from.isBlank()) return """{"error":"fromCity is required"}"""
    if (to.isBlank()) return """{"error":"toCity is required"}"""
    if (date.isBlank()) return """{"error":"date is required (YYYY-MM-DD)"}"""
    if (!isValidIsoDate(date)) return """{"error":"date must be YYYY-MM-DD","date":"${escapeJson(date)}"}"""
    return null
}

private fun isValidIsoDate(s: String): Boolean {
    return try {
        LocalDate.parse(s)
        true
    } catch (_: DateTimeParseException) {
        false
    }
}

// ---------- CSV loaders ----------

private fun loadTrainsFromCsv(resourcePath: String): List<TrainTrip> {
    val stream = object {}.javaClass.getResourceAsStream(resourcePath)
        ?: throw IllegalStateException("Resource not found: $resourcePath (put it in src/main/resources)")
    BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).use { br ->
        val lines = br.lineSequence().toList()
        if (lines.isEmpty()) return emptyList()
        // header:
        // id,fromCity,toCity,date,departTime,arriveTime,durationMin,train,seatClass,priceRub,seatsLeft
        return lines.drop(1)
            .filter { it.isNotBlank() && !it.trim().startsWith("#") }
            .map { line ->
                val p = line.split(",").map { it.trim() }
                require(p.size >= 11) { "Bad trains CSV line: $line" }
                TrainTrip(
                    id = p[0],
                    fromCity = p[1],
                    toCity = p[2],
                    date = p[3],
                    departTime = p[4],
                    arriveTime = p[5],
                    durationMin = p[6].toInt(),
                    train = p[7],
                    seatClass = p[8],
                    priceRub = p[9].toInt(),
                    seatsLeft = p[10].toInt()
                )
            }
    }
}

private fun loadFlightsFromCsv(resourcePath: String): List<FlightTrip> {
    val stream = object {}.javaClass.getResourceAsStream(resourcePath)
        ?: throw IllegalStateException("Resource not found: $resourcePath (put it in src/main/resources)")
    BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).use { br ->
        val lines = br.lineSequence().toList()
        if (lines.isEmpty()) return emptyList()
        // header:
        // id,fromCity,toCity,date,departTime,arriveTime,durationMin,airline,priceRub,baggage
        return lines.drop(1)
            .filter { it.isNotBlank() && !it.trim().startsWith("#") }
            .map { line ->
                val p = line.split(",").map { it.trim() }
                require(p.size >= 10) { "Bad flights CSV line: $line" }
                FlightTrip(
                    id = p[0],
                    fromCity = p[1],
                    toCity = p[2],
                    date = p[3],
                    departTime = p[4],
                    arriveTime = p[5],
                    durationMin = p[6].toInt(),
                    airline = p[7],
                    priceRub = p[8].toInt(),
                    baggage = p[9]
                )
            }
    }
}

// ---------- Taxi JSON loader (минимальный парсер под нашу структуру) ----------

private fun loadTaxiRulesFromJson(resourcePath: String): List<TaxiRule> {
    val stream = object {}.javaClass.getResourceAsStream(resourcePath)
        ?: throw IllegalStateException("Resource not found: $resourcePath (put it in src/main/resources)")
    val json = stream.bufferedReader(Charsets.UTF_8).readText()

    // Ожидаемый формат:
    // { "rules": [ { "city":"Москва", "baseRub":260, "perKmRub":32, "surge":1.10, "notes":"..." }, ... ] }
    val rulesBlock = Regex("\"rules\"\\s*:\\s*\\[(.*)]", RegexOption.DOT_MATCHES_ALL)
        .find(json)?.groupValues?.get(1) ?: return emptyList()

    val objRegex = Regex("\\{(.*?)\\}", RegexOption.DOT_MATCHES_ALL)
    return objRegex.findAll(rulesBlock).map { m ->
        val obj = m.groupValues[1]
        fun str(key: String): String =
            Regex("\"$key\"\\s*:\\s*\"(.*?)\"", RegexOption.DOT_MATCHES_ALL).find(obj)?.groupValues?.get(1) ?: ""
        fun int(key: String): Int =
            Regex("\"$key\"\\s*:\\s*(\\d+)").find(obj)?.groupValues?.get(1)?.toInt() ?: 0
        fun dbl(key: String): Double =
            Regex("\"$key\"\\s*:\\s*([0-9]+\\.[0-9]+|[0-9]+)").find(obj)?.groupValues?.get(1)?.toDouble() ?: 1.0

        TaxiRule(
            city = str("city"),
            baseRub = int("baseRub"),
            perKmRub = int("perKmRub"),
            surge = dbl("surge"),
            notes = str("notes")
        )
    }.toList()
}

// ---------- JSON helpers ----------

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