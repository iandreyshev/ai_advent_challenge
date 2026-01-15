# Архитектура системы поддержки TaskFlow

## Общая схема

```
┌─────────────────────────────────────────────────────────────────┐
│                    Support Assistant (Kotlin)                    │
│                                                                   │
│  ┌──────────────────┐        ┌──────────────────┐              │
│  │   RAG System     │        │  YandexGPT API   │              │
│  │                  │        │   (optional)     │              │
│  │  - VectorStore   │        └──────────────────┘              │
│  │  - Doc Indexing  │                │                          │
│  │  - Similarity    │                │                          │
│  │    Search        │                │                          │
│  └────────┬─────────┘                │                          │
│           │                          │                          │
│           v                          v                          │
│  ┌─────────────────────────────────────────┐                   │
│  │      Ollama (Local Embeddings)          │                   │
│  │                                         │                   │
│  │  - nomic-embed-text (embeddings)       │                   │
│  │  - llama2/llama3 (fallback LLM)        │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                   │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        │ HTTP
                        v
┌─────────────────────────────────────────────────────────────────┐
│                  MCP Server (Ktor + Kotlin)                      │
│                                                                   │
│  MCP Tools:                                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ 1. get_user_info(userId)                              │      │
│  │    → Информация о пользователе (план, статус)        │      │
│  │                                                        │      │
│  │ 2. get_ticket(ticketId)                               │      │
│  │    → Детали тикета с контекстом пользователя         │      │
│  │                                                        │      │
│  │ 3. search_tickets(filters)                            │      │
│  │    → Поиск тикетов по статусу/категории/приоритету   │      │
│  │                                                        │      │
│  │ 4. get_user_tickets(userId)                           │      │
│  │    → История обращений пользователя                   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                   │
│  Data Source:                                                    │
│  └─ support.json (Users + Tickets)                              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘


Documentation Source:
┌─────────────────────────────────────┐
│      docs/ directory (TXT)          │
│                                     │
│  - authentication.txt               │
│  - tasks.txt                        │
│  - notifications.txt                │
│  - sync.txt                         │
│  - billing.txt                      │
│  - faq.txt                          │
└─────────────────────────────────────┘
```

## Поток обработки запроса

```
1. User Question
   "Почему не работает авторизация через Google?"
   userId: user001
   ticketId: ticket001
        │
        v
┌─────────────────────────────────────────────────────────┐
│ 2. RAG: Retrieve Relevant Documentation                 │
│                                                          │
│    Question → Ollama Embedding → Vector Search          │
│                                                          │
│    Result: Top-3 relevant chunks                        │
│    - authentication.txt: OAuth section                  │
│    - faq.txt: common auth issues                        │
│    - authentication.txt: troubleshooting                │
└─────────────────────────────────────────────────────────┘
        │
        v
┌─────────────────────────────────────────────────────────┐
│ 3. MCP: Get User & Ticket Context                       │
│                                                          │
│    get_user_info(user001)                               │
│    → Name: Иван Петров                                  │
│    → Plan: Pro                                          │
│    → Status: Active                                     │
│                                                          │
│    get_ticket(ticket001)                                │
│    → Subject: OAuth не работает                         │
│    → Description: Invalid redirect URI                  │
│    → Status: Open, Priority: High                       │
│                                                          │
│    get_user_tickets(user001)                            │
│    → Previous ticket: billing question (resolved)       │
└─────────────────────────────────────────────────────────┘
        │
        v
┌─────────────────────────────────────────────────────────┐
│ 4. Context Assembly                                      │
│                                                          │
│    Combined Context:                                    │
│    ┌────────────────────────────────────────┐          │
│    │ === DOCUMENTATION ===                   │          │
│    │ OAuth аутентификация...                │          │
│    │ Ошибка Invalid redirect URI...         │          │
│    │                                         │          │
│    │ === USER CONTEXT ===                   │          │
│    │ User: Иван Петров (Pro plan)          │          │
│    │ Current ticket: OAuth проблема         │          │
│    │ Previous: 1 resolved ticket            │          │
│    └────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────┘
        │
        v
┌─────────────────────────────────────────────────────────┐
│ 5. Answer Generation                                     │
│                                                          │
│    IF YandexGPT configured:                             │
│       → YandexGPT API with full context                 │
│    ELSE:                                                │
│       → Ollama (llama2/llama3) as fallback              │
│                                                          │
│    Generated answer with:                               │
│    - Problem explanation                                │
│    - Step-by-step solution                              │
│    - User-specific considerations (Pro plan features)   │
└─────────────────────────────────────────────────────────┘
        │
        v
    Answer returned to user
```

## Компоненты

### 1. Support Assistant (Клиент)

**Файлы:**
- `Main.kt` - точка входа, инициализация
- `SupportAssistant.kt` - главный оркестратор
- `RAGSystem.kt` - RAG логика
- `VectorStore.kt` - in-memory векторная БД
- `OllamaClient.kt` - клиент для Ollama
- `YandexAgentClient.kt` - клиент для YandexGPT

**Функции:**
- Индексация документации при старте
- Векторный поиск по документам
- Обращение к MCP-серверу за контекстом
- Генерация ответа через LLM

### 2. MCP Server (Сервер контекста)

**Файлы:**
- `Application.kt` - Ktor приложение
- `MCPServer.kt` - MCP инструменты
- `Routing.kt` - HTTP routing
- `support.json` - данные (пользователи, тикеты)

**Функции:**
- Предоставление MCP инструментов
- Доступ к "CRM" данным
- REST API для клиента

### 3. Documentation (База знаний)

**Формат:** Plain text файлы (.txt)

**Структура:**
- Заголовки с решетками (#, ##)
- Подробные инструкции
- Типичные проблемы и решения
- FAQ секции

**Процесс:**
1. Документы разбиваются на чанки (500 слов, overlap 50)
2. Каждый чанк конвертируется в эмбеддинг
3. Хранится в векторной БД с метаданными

## Технологии

### Backend (MCP Server)
- **Kotlin** 2.2.21
- **Ktor** 3.3.2 (HTTP сервер)
- **MCP SDK** (Model Context Protocol)
- **JSON** для хранения данных

### Client (Support Assistant)
- **Kotlin** 2.2.21
- **Ktor Client** (HTTP клиент)
- **Ollama** (локальные эмбеддинги)
- **YandexGPT** (опционально)

### AI/ML
- **nomic-embed-text** - модель эмбеддингов (Ollama)
- **YandexGPT** - генерация ответов
- **Cosine Similarity** - поиск похожих документов

## Масштабируемость

### Текущая реализация (MVP)
- In-memory векторная БД
- JSON для данных
- Синхронная обработка

### Возможные улучшения

1. **Векторная БД:**
   - PostgreSQL + pgvector
   - Qdrant / Weaviate / Pinecone
   - ChromaDB

2. **Хранилище:**
   - PostgreSQL вместо JSON
   - Redis для кэширования

3. **Производительность:**
   - Асинхронная индексация
   - Batch processing эмбеддингов
   - Кэширование часто запрашиваемых документов

4. **Функциональность:**
   - Переранжирование результатов
   - Гибридный поиск (keyword + semantic)
   - История диалогов
   - A/B тестирование промптов

5. **Мониторинг:**
   - Метрики качества ответов
   - Время ответа
   - Использование контекста

## Безопасность

### Реализовано
- Локальные эмбеддинги (данные не уходят вовне)
- API ключи через environment variables

### Рекомендации
- Rate limiting для API
- Аутентификация пользователей
- Шифрование чувствительных данных
- Аудит логи доступа к тикетам

## Развертывание

### Development
- Ollama локально
- MCP сервер: `./gradlew run`
- Client: `./gradlew run`

### Production (рекомендации)

1. **MCP Server:**
   ```bash
   ./gradlew build
   docker build -t support-mcp .
   docker run -p 8080:8080 support-mcp
   ```

2. **Support Assistant:**
   ```bash
   ./gradlew build
   java -jar build/libs/support-assistant.jar
   ```

3. **Ollama:**
   - Self-hosted сервер
   - Или использовать только YandexGPT

4. **Reverse Proxy:**
   - Nginx перед MCP сервером
   - SSL/TLS сертификаты
   - Rate limiting

## Мониторинг и метрики

### Ключевые метрики
- Время индексации документов
- Время поиска по векторам
- Время генерации ответа
- Relevance score документов
- Качество ответов (user feedback)

### Логирование
- Structured logging (JSON)
- Request/Response logging
- Error tracking (Sentry)

## Тестирование

### Unit тесты
- VectorStore (cosine similarity)
- Document chunking
- MCP tools

### Integration тесты
- Ollama connectivity
- MCP server endpoints
- End-to-end query flow

### E2E тесты
- Полный цикл вопрос-ответ
- Различные типы вопросов
- Edge cases

## Лицензия

MIT
