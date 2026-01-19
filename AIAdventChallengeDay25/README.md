# Ollama Chat

Простое консольное приложение для общения с локальными LLM через Ollama.

## Требования

- Python 3.6+
- [Ollama](https://ollama.ai/) установлен и запущен

## Установка модели

```bash
ollama pull qwen2.5
```

## Запуск сервера Ollama

Перед использованием чата убедитесь, что сервер Ollama запущен:

```bash
ollama serve
```

## Запуск

```bash
python3 chat.py
```

Или с указанием другой модели:

```bash
python3 chat.py llama3.2
```

## Команды в чате

- `выход`, `exit`, `quit` — завершить чат
- `Ctrl+C` — принудительный выход
