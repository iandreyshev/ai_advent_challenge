# День 14: Travel Planning Suite (3 MCP сервера)

Набор из трёх MCP серверов для планирования путешествий.

## Серверы

### 1. hotels-mcp — Поиск отелей
| Tool | Описание |
|------|----------|
| `search_hotels` | Поиск отелей по городу (цена, звёзды, метро) |
| `get_hotel_details` | Детали конкретного отеля |

### 2. itinerary-mcp — Маршруты
| Tool | Описание |
|------|----------|
| `get_attractions` | Достопримечательности (категория, цена, открыто сейчас) |
| `build_3day_itinerary` | Маршрут на 3 дня (город, темп, бюджет) |

### 3. transport-mcp — Транспорт
| Tool | Описание |
|------|----------|
| `search_trains` | Поиск поездов |
| `search_flights` | Поиск авиарейсов |
| `estimate_taxi` | Оценка стоимости такси |

## Технологии

- **Kotlin** — основной язык
- **Ktor** — HTTP серверы
- **MCP SDK** — протокол
- **kotlinx.serialization** — JSON

## Структура

```
AIAdventChallengeDay14/
├── hotels-mcp/
│   ├── src/main/kotlin/
│   └── hotels.csv           # Тестовые данные
├── itinerary-mcp/
│   ├── src/main/kotlin/
│   └── attractions.json     # Тестовые данные
└── transport-mcp/
    ├── src/main/kotlin/
    ├── trains.csv
    ├── flights.csv
    └── taxi_rules.json
```

## Запуск

```bash
# Каждый сервер запускается отдельно
cd hotels-mcp && ./gradlew run
cd itinerary-mcp && ./gradlew run
cd transport-mcp && ./gradlew run
```

## Особенности

- Все три сервера могут подключаться к LLM одновременно
- File-based данные (CSV, JSON) для демонстрации
- Фильтрация и сортировка результатов
