# RAG Development Assistant

AI-ассистент для помощи в разработке с использованием RAG (Retrieval-Augmented Generation) и MCP (Model Context Protocol).

> **AI Advent Challenge Day 20**: Создание ассистента разработчика с RAG и MCP интеграцией

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Возможности

### RAG-поиск по документации
- Семантический поиск по всей документации проекта
- Индексация Markdown, Python, JavaScript файлов
- Векторная база данных ChromaDB
- Embeddings через Voyage AI (с fallback)

### Git-интеграция через MCP
- Информация о текущей ветке
- История коммитов
- Статус изменений (modified, staged, untracked)
- Diff анализ

### Команда /help
- Интеллектуальные ответы на вопросы о проекте
- Примеры кода из документации с указанием источников
- Рекомендации по стилю кода
- Информация об API endpoints и database schema

## Быстрый старт

```bash
# 1. Установка
bash setup.sh

# 2. Настройка .env (добавьте ваши API ключи)
cp .env.example .env

# 3. Индексация документации
make index

# 4. Запуск ассистента
make assistant
```

См. [QUICKSTART.md](QUICKSTART.md) для подробных инструкций.

## Архитектура

```
┌─────────────────────────────────────┐
│      Development Assistant          │
│  ┌──────────┐  ┌──────┐  ┌───────┐ │
│  │   RAG    │  │ MCP  │  │Claude │ │
│  │  System  │  │Server│  │  API  │ │
│  └─────┬────┘  └───┬──┘  └───────┘ │
└────────┼───────────┼────────────────┘
         │           │
    ┌────▼─────┐ ┌──▼───┐
    │ChromaDB  │ │ Git  │
    │ Vectors  │ │ Repo │
    └──────────┘ └──────┘
```

См. [ARCHITECTURE.md](ARCHITECTURE.md) для детального описания.

## Технологии

| Компонент | Технология | Описание |
|-----------|-----------|----------|
| LLM | Claude Opus 4.5 | Основная модель для ответов |
| Vector DB | ChromaDB | Хранение embeddings |
| Embeddings | Voyage AI | Генерация векторов |
| Git | GitPython | Интеграция с репозиторием |
| CLI | Click + Rich | Пользовательский интерфейс |
| MCP | Custom | Протокол контекста модели |

## Использование

### Interactive Mode

```bash
$ python -m src.assistant.cli interactive

You: Как работает аутентификация?
Assistant: Based on API.md, authentication uses JWT...

You: git
Current Branch: main
Status: 3 modified, 0 staged, 0 untracked
```

### Command Line

```bash
# Получить помощь
python -m src.assistant.cli help "Какие API endpoints доступны?"

# Поиск в документации
python -m src.assistant.cli search "authentication"

# Найти связанные файлы
python -m src.assistant.cli files "error handling"

# Git контекст
python -m src.assistant.cli git
```

### Makefile Shortcuts

```bash
make help        # Показать доступные команды
make setup       # Установка окружения
make index       # Индексация документации
make assistant   # Запуск интерактивного режима
make git         # Показать git контекст
make clean       # Очистка
```

## Примеры вопросов

- ❓ "Как работает аутентификация в этом проекте?"
- ❓ "Какие API endpoints доступны?"
- ❓ "Покажи пример обработки ошибок"
- ❓ "Что такое схема базы данных для пользователей?"
- ❓ "Какой стиль кода я должен использовать?"
- ❓ "Как сделать commit в этом проекте?"

См. [EXAMPLES.md](docs/EXAMPLES.md) для реальных примеров использования.

## Структура проекта

```
AIAdventChallengeDay20/
├── docs/                    # Документация (индексируется RAG)
│   ├── API.md              # API endpoints
│   ├── STYLE_GUIDE.md      # Стиль кода
│   └── DATABASE_SCHEMA.md  # Схема БД
│
├── src/
│   ├── rag/                # RAG система
│   │   ├── embeddings.py   # Генерация embeddings
│   │   ├── indexer.py      # Индексация
│   │   └── retriever.py    # Поиск
│   │
│   ├── mcp/                # MCP сервер
│   │   ├── git_tools.py    # Git операции
│   │   └── server.py       # MCP сервер
│   │
│   └── assistant/          # AI ассистент
│       ├── assistant.py    # Основная логика
│       └── cli.py          # CLI интерфейс
│
├── requirements.txt        # Зависимости
├── setup.sh               # Скрипт установки
└── Makefile               # Команды
```

См. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) для полной структуры.

## Конфигурация

### Environment Variables (.env)

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional (will use fallback)
VOYAGE_API_KEY=pa-your-key-here

# RAG Settings
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5

# Paths
DOCS_PATH=./docs
PROJECT_ROOT=.
```

### RAG Settings

Настраиваются в `src/rag/config.py`:
- **Chunk size**: 500 tokens
- **Chunk overlap**: 50 tokens
- **Top-K results**: 5
- **Vector dimension**: 384

### MCP Tools

Доступные инструменты:
- `get_current_branch` - Текущая ветка
- `get_git_status` - Статус изменений
- `get_recent_commits` - История коммитов
- `get_file_history` - История файла
- `get_branches` - Все ветки
- `get_remote_info` - Информация о remote
- `get_diff` - Git diff

## Тестирование

```bash
# Запуск тестов системы
python test_system.py

# Тесты проверяют:
✓ Directory Structure
✓ Documentation
✓ Imports
✓ Document Chunker
✓ Git Tools
✓ MCP Server
✓ Embeddings
```

## Документация

- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архитектура системы
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Структура проекта
- [docs/USAGE.md](docs/USAGE.md) - Инструкции по использованию
- [docs/EXAMPLES.md](docs/EXAMPLES.md) - Примеры использования
- [docs/API.md](docs/API.md) - API документация
- [docs/STYLE_GUIDE.md](docs/STYLE_GUIDE.md) - Стиль кода
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - Схема БД

## Требования

- Python 3.8+
- Anthropic API key (Claude)
- Voyage AI API key (опционально)
- Git repository (для MCP)

## Установка зависимостей

```bash
pip install -r requirements.txt
```

### Основные зависимости

- anthropic >= 0.40.0
- chromadb >= 0.4.22
- voyageai >= 0.2.3
- GitPython >= 3.1.40
- click >= 8.1.7
- rich >= 13.7.0

## Как это работает

1. **Индексация**: Документация разбивается на chunks и индексируется в ChromaDB
2. **Запрос**: Пользователь задает вопрос
3. **Retrieval**: RAG находит релевантные документы
4. **Context**: MCP добавляет git контекст
5. **Generation**: Claude генерирует ответ на основе контекста
6. **Response**: Форматированный ответ с источниками

## Примеры ответов

### Вопрос об API
```
You: Какие API endpoints доступны?