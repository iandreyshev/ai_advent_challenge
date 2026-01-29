# День 12: MCP сервер для iSpring Learn

Kotlin MCP-сервер для интеграции с iSpring Learn REST API.

## Возможности

- MCP сервер на Ktor
- Интеграция с iSpring Learn API
- Кэширование OAuth токенов
- SSE транспорт для MCP протокола

## MCP Tools

| Tool | Описание |
|------|----------|
| `get_users` | Получить список пользователей с фильтрацией по отделам/группам |
| `get_user_info` | Получить информацию о конкретном пользователе по ID |

## Технологии

- **Kotlin** — основной язык
- **Ktor** — HTTP сервер
- **MCP SDK** — `io.modelcontextprotocol:kotlin-sdk`
- **SSE** — Server-Sent Events

## Структура

```
AIAdventChallengeDay12/
└── FirstMCP/
    ├── src/main/kotlin/
    │   ├── Application.kt       # Точка входа
    │   ├── MCPServer.kt         # Конфигурация MCP
    │   ├── Routing.kt           # HTTP роуты
    │   └── ISpringLearnClient.kt # API клиент
    └── build.gradle.kts
```

## Запуск

```bash
cd FirstMCP
./gradlew run
```

## Конфигурация

Создайте файл с секретами для iSpring Learn API:
- Account URL
- Client ID
- Client Secret

## Зависимости

```kotlin
io.ktor:ktor-server-core-jvm
io.ktor:ktor-server-netty
io.modelcontextprotocol:kotlin-sdk
ch.qos.logback:logback-classic
```
