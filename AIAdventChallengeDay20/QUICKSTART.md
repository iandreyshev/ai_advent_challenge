# Quick Start Guide

## Установка и запуск за 5 минут

### 1. Установка зависимостей

```bash
# Автоматическая установка
bash setup.sh

# Или вручную
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка API ключей

Отредактируйте файл `.env`:

```bash
# Обязательно
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Опционально (будет использоваться fallback)
VOYAGE_API_KEY=pa-your-key-here
```

### 3. Индексация документации

```bash
make index
# или
python -m src.assistant.cli index
```

### 4. Запуск ассистента

```bash
make assistant
# или
python -m src.assistant.cli interactive
```

## Быстрые команды

```bash
# Получить помощь
python -m src.assistant.cli help "Как работает аутентификация?"

# Поиск в документации
python -m src.assistant.cli search "API endpoints"

# Git контекст
python -m src.assistant.cli git

# Найти связанные файлы
python -m src.assistant.cli files "authentication"
```

## Что делает ассистент?

### ✅ RAG (Retrieval-Augmented Generation)
- Индексирует всю документацию проекта
- Семантический поиск по документам
- Контекстные ответы на основе документации

### ✅ MCP (Model Context Protocol)
- Интеграция с git репозиторием
- Информация о текущей ветке
- История коммитов
- Статус изменений

### ✅ Команда /help
- Интеллектуальные ответы о проекте
- Примеры кода из документации
- Рекомендации по стилю кода
- Информация об API и БД

## Примеры использования

### Вопросы о проекте

```bash
$ python -m src.assistant.cli help "Какие эндпоинты есть в API?"