# Code Style Guide

## Python Style Guide

### Общие правила

- Следуем PEP 8
- Максимальная длина строки: 100 символов
- Используем type hints для всех функций
- Docstrings в Google style

### Именование

```python
# Классы: PascalCase
class UserManager:
    pass

# Функции и переменные: snake_case
def get_user_by_id(user_id: str) -> User:
    pass

# Константы: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# Приватные методы/атрибуты: префикс _
def _internal_method(self):
    pass
```

### Imports

```python
# Порядок импортов:
# 1. Стандартная библиотека
# 2. Сторонние библиотеки
# 3. Локальные модули

import os
import sys
from typing import Optional, List

import anthropic
import chromadb
from fastapi import FastAPI

from src.rag.indexer import DocumentIndexer
from src.models import User
```

### Type Hints

```python
from typing import Optional, List, Dict, Any

def process_documents(
    documents: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """
    Process a list of documents.

    Args:
        documents: List of document texts
        config: Optional configuration dictionary

    Returns:
        Dictionary with processing statistics
    """
    pass
```

### Error Handling

```python
# Используем специфичные исключения
class DocumentNotFoundError(Exception):
    """Raised when document is not found."""
    pass

# Try-except с конкретными исключениями
try:
    result = process_document(doc)
except DocumentNotFoundError as e:
    logger.error(f"Document not found: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Уровни логирования:
logger.debug("Detailed information for debugging")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.exception("Error with traceback")
```

### Async Code

```python
import asyncio
from typing import List

async def fetch_data(url: str) -> dict:
    """Fetch data asynchronously."""
    pass

async def process_all(urls: List[str]) -> List[dict]:
    """Process multiple URLs concurrently."""
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## Git Commit Messages

### Формат

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: Новая функциональность
- `fix`: Исправление бага
- `docs`: Изменения в документации
- `style`: Форматирование кода
- `refactor`: Рефакторинг
- `test`: Добавление тестов
- `chore`: Обновление зависимостей, конфигурации

### Примеры

```
feat(rag): add semantic search with ChromaDB

Implemented vector database integration for document search.
Added embedding generation using Voyage AI.

Closes #123
```

```
fix(mcp): handle git errors gracefully

Fixed crash when git repository is not initialized.
```

## Testing

### Структура тестов

```python
import pytest
from src.rag.indexer import DocumentIndexer

class TestDocumentIndexer:
    @pytest.fixture
    def indexer(self):
        return DocumentIndexer(collection_name="test")

    def test_index_document(self, indexer):
        """Test document indexing."""
        doc_id = indexer.add_document("Test content")
        assert doc_id is not None

    @pytest.mark.asyncio
    async def test_async_search(self, indexer):
        """Test async search."""
        results = await indexer.search_async("query")
        assert len(results) > 0
```

### Coverage

- Минимальное покрытие: 80%
- Запуск: `pytest --cov=src --cov-report=html`

## Code Review Checklist

- [ ] Код следует style guide
- [ ] Добавлены type hints
- [ ] Написаны docstrings
- [ ] Добавлены тесты
- [ ] Нет hardcoded значений
- [ ] Обработка ошибок
- [ ] Логирование добавлено где нужно
- [ ] Документация обновлена
