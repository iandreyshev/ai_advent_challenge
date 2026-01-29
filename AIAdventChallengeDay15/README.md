# День 15: Docker Toggle MCP

MCP сервер для управления Docker контейнерами.

## Возможности

- Запуск и остановка Docker Compose стека
- Управление через MCP протокол
- Перехват stdout/stderr

## MCP Tools

| Tool | Описание |
|------|----------|
| `start_docker_server` | Запустить docker compose (web-сервер на порту 8080) |
| `stop_docker_server` | Остановить docker compose |

## Технологии

- **Kotlin** — основной язык
- **Ktor** — HTTP сервер
- **MCP SDK** — протокол
- **ProcessBuilder** — выполнение shell команд

## Структура

```
AIAdventChallengeDay15/
└── docker-mcp/
    ├── src/main/kotlin/
    │   ├── Application.kt
    │   ├── MCPServer.kt
    │   └── Routing.kt
    ├── docker-compose.yml
    └── build.gradle.kts
```

## Запуск

```bash
cd docker-mcp
./gradlew run
```

## Как работает

1. MCP сервер получает команду `start_docker_server`
2. Выполняет `docker compose up -d`
3. Возвращает результат (код выхода, stdout, stderr)

## Особенности

- JSON ответы с полной информацией о выполнении
- Обработка ошибок Docker
- Автоматический откат при сбоях
