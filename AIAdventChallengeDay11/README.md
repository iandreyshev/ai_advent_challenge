# День 11: MCP Client

iOS-приложение для подключения к Model Context Protocol (MCP) серверу.

## Возможности

- Подключение к MCP серверу через HTTP
- Загрузка списка доступных tools
- Bearer token авторизация
- Проверка capabilities сервера

## Технологии

- **SwiftUI** — пользовательский интерфейс
- **MCP SDK** — Model Context Protocol
- **HTTPClientTransport** — HTTP транспорт для MCP
- **SSE** — Server-Sent Events

## Model Context Protocol

MCP — это протокол для расширения возможностей LLM через внешние инструменты:

```
iOS App → MCP Server → Tools (APIs, DBs, etc.)
```

## Структура

```
AIAdventChallengeDay11/
├── ContentView.swift    # UI и MCP клиент
├── Secrets.swift        # Endpoint и токен (gitignored)
└── Assets/
```

## Настройка

1. Добавьте в `Secrets.swift`:
```swift
enum Secrets {
    static let mcpEndpoint = "https://your-mcp-server.com"
    static let authToken = "your-bearer-token"
}
```

2. Откройте в Xcode и запустите

## Особенности

- Потоковая обработка (streaming: true)
- Проверка наличия tools capability
- Отображение списка инструментов сервера
