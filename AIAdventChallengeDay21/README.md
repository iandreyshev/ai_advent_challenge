# День 21: Code Reviewer

Утилита для автоматического code review через Yandex Agent.

## Возможности

- Получение diff между ветками Git
- Отправка кода на review в Yandex Agent
- Автоматический анализ изменений
- Вывод результатов review

## Технологии

- **Kotlin** — основной язык
- **Yandex Agent API** — review
- **Git** — работа с репозиторием
- **OkHttp** — HTTP клиент

## Использование

```bash
./gradlew run --args="<source-branch> <target-branch>"

# Пример
./gradlew run --args="feature/new-api main"
```

## Компоненты

| Класс | Описание |
|-------|----------|
| `GitRepository` | Работа с Git (diff, файлы) |
| `YandexAgentClient` | Интеграция с Yandex Agent |

## Структура

```
AIAdventChallengeDay21/
└── reviewer-mcp/
    ├── src/main/kotlin/
    │   ├── GitRepository.kt
    │   └── YandexAgentClient.kt
    └── build.gradle.kts
```

## Переменные окружения

```bash
export YANDEX_API_KEY="..."
export YANDEX_FOLDER_ID="..."
export YANDEX_AGENT_ID="..."
export REPOSITORY_PATH="/path/to/repo"
```

## Зависимости

```kotlin
com.squareup.okhttp3:okhttp:4.12.0
com.fasterxml.jackson.*
org.json:json
ch.qos.logback:logback-classic
```

## Применение

- CI/CD интеграция
- Автоматический review PR
- Проверка качества кода
