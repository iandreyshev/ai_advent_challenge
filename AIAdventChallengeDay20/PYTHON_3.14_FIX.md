# Python 3.14 Compatibility Fix

## Проблема

ChromaDB не совместим с Python 3.14 из-за зависимости от Pydantic V1.

## Решение

Проект автоматически использует fallback на простую in-memory векторную БД, если ChromaDB не работает.

## Что изменено

1. **Создан `src/rag/simple_vectordb.py`** - простая векторная БД на numpy
2. **Обновлен `src/rag/indexer.py`** - автоматический fallback
3. **Обновлен `src/rag/retriever.py`** - автоматический fallback

## Установка

Теперь просто запустите:

```bash
pip install -r requirements.txt
```

При запуске вы увидите сообщение:

```
ChromaDB not available (...), using simple fallback vector DB
```

Это **нормально**! Система будет работать с fallback реализацией.

## Функциональность

Все возможности работают:

✅ Индексация документации
✅ Семантический поиск
✅ RAG для ответов
✅ Persistence (данные сохраняются в JSON)
✅ Metadata фильтрация

## Использование

Команды остаются те же:

```bash
# Индексация
python -m src.assistant.cli index

# Поиск
python -m src.assistant.cli search "authentication"

# Ассистент
python -m src.assistant.cli interactive
```

## Альтернатива: использовать Python 3.11

Если вы хотите использовать оригинальный ChromaDB:

```bash
# Удалить текущее окружение
rm -rf venv

# Создать с Python 3.11
python3.11 -m venv venv
source venv/bin/activate

# Установить с оригинальным ChromaDB
pip install chromadb>=0.4.22 anthropic voyageai GitPython click rich python-dotenv numpy
```

## Что лучше?

**Для демонстрации проекта**: текущий fallback вариант отлично работает
**Для production**: используйте Python 3.11 + ChromaDB

## Отличия fallback версии

| Функция | ChromaDB | Fallback |
|---------|----------|----------|
| Индексация | ✅ | ✅ |
| Поиск | ✅ | ✅ |
| Persistence | SQLite | JSON |
| Скорость | Быстрее | Медленнее на больших данных |
| Память | Эффективнее | Все в RAM |
| Масштабируемость | Отлично | Ограничено |

Для документации проекта (несколько файлов .md) **разницы не заметно**.

## Проверка

Запустите тесты:

```bash
python test_system.py
```

Все должно работать!
