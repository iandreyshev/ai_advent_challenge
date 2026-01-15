# Быстрый старт

## Подготовка (5 минут)

### 1. Установить Ollama
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Загрузить модель
```bash
ollama pull nomic-embed-text
```

### 3. Запустить Ollama
```bash
ollama serve
```

## Запуск (2 минуты)

### Терминал 1: MCP-сервер
```bash
cd hotels-mcp
./gradlew run
```

Дождитесь сообщения: `Application started`

### Терминал 2: Ассистент
```bash
cd support-assistant
./gradlew run
```

## Что произойдет

1. Загрузка и индексация документации (~30 сек)
2. Автоматический запуск 3 тестовых запросов
3. Вывод ответов в консоль

## Тестовые вопросы

1. "Почему не работает авторизация через Google?"
2. "Не могу создать задачу, кнопка не работает"
3. "Не приходят уведомления на email"

## Ожидаемый результат

Для каждого вопроса:
- Найдены релевантные документы
- Получен контекст пользователя и тикета
- Сгенерирован подробный ответ

## Опционально: Yandex Cloud

Для использования YandexGPT вместо Ollama:

```bash
export YANDEX_API_KEY="your_key"
export YANDEX_FOLDER_ID="your_folder"
```

Затем перезапустите `support-assistant`

## Troubleshooting

**Ollama не отвечает:**
```bash
curl http://localhost:11434/api/tags
```

**Порт 8080 занят:**
Измените в `hotels-mcp/src/main/resources/application.yaml`:
```yaml
ktor:
  deployment:
    port: 8081  # другой порт
```

**Документация не найдена:**
Проверьте путь в `support-assistant/src/main/kotlin/.../Main.kt`:
```kotlin
val docsPath = "../hotels-mcp/src/main/resources/docs"
```

## Структура данных

- **Пользователи:** 4 тестовых аккаунта (Free, Pro, Business планы)
- **Тикеты:** 7 обращений (authentication, tasks, notifications, etc.)
- **Документация:** 6 файлов (auth, tasks, notifications, sync, billing, FAQ)

## Дальше

Смотрите полную документацию в [README.md](README.md)
