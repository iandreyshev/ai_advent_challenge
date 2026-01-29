# День 13: Сервис напоминаний (MCP + Push)

Комплексное решение для напоминаний: MCP сервер, Push Sender и мобильный клиент.

## Компоненты

### 1. RemindersMCP
MCP сервер для получения активных напоминаний из Firestore.

### 2. PushNotificationSender
Standalone приложение для отправки push-уведомлений через Firebase.

### 3. MobileReminderClient
Мобильный клиент для работы с напоминаниями.

## MCP Tools

| Tool | Описание |
|------|----------|
| `get_active_reminders` | Получить активные напоминания из Firestore с лимитом |

## Технологии

- **Kotlin** — основной язык
- **Ktor** — HTTP сервер
- **Firebase Admin SDK** — push уведомления
- **Firestore** — база данных
- **MCP SDK** — протокол

## Структура

```
AIAdventChallengeDay13/
├── RemindersMCP/           # MCP сервер
│   └── src/main/kotlin/
├── PushNotificationSender/ # Push отправщик
│   └── src/main/kotlin/
└── MobileReminderClient/   # Мобильный клиент
```

## Запуск MCP сервера

```bash
cd RemindersMCP
./gradlew run
```

## Запуск Push Sender

```bash
cd PushNotificationSender
./gradlew run
```

## Особенности

- Временные зоны (Moscow timezone)
- JSON escape для безопасности
- Интеграция с Yandex Agent для генерации текста уведомлений
