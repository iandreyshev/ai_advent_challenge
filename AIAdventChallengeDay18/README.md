# День 18: AI Search в Telegram чатах

Утилита для семантического поиска по экспортированным Telegram чатам с использованием RAG.

## Возможности

- Парсинг Telegram chat export (JSON)
- Построение векторного индекса
- Семантический поиск по сообщениям
- Интерактивный режим с top-5 результатами

## Технологии

- **Kotlin** — основной язык
- **Ollama** — embeddings (snowflake-arctic-embed2)
- **Yandex Agent** — генерация ответов
- **OkHttp** — HTTP клиент
- **Jackson** — JSON парсинг

## Компоненты

| Модуль | Описание |
|--------|----------|
| `ChatParser` | Парсинг Telegram export |
| `ChatChunker` | Разбиение на chunks |
| `OllamaEmbedClient` | Работа с embeddings |
| `YandexLlmClient` | Генерация через Yandex |
| `RagSearch` | Cosine similarity поиск |
| `JsonlIndex` | Хранение индекса |

## Структура

```
AIAdventChallengeDay18/
└── ai-search-in-tg/
    ├── src/main/kotlin/
    │   ├── ai/      # LLM клиенты
    │   ├── rag/     # RAG логика
    │   ├── tg/      # Telegram парсер
    │   └── utils/   # Утилиты
    └── build.gradle.kts
```

## Использование

```bash
# Построить индекс
./gradlew run --args="--build-index"

# Интерактивный поиск
./gradlew run
```

## Команды в интерактивном режиме

- `/exit` — выход
- `/help` — справка
- Любой текст — поиск

## Параметры

```
OLLAMA_EMBED_URL: http://localhost:11434/api/embeddings
N_MESSAGES_PER_CHUNK: 12
MAX_CHUNK_CHARS: 2500
TOP_K_PER_QUERY: 50
```
