#!/usr/bin/env python3
"""
День 29: Локальный аналитик данных.

Использует Ollama для анализа CSV и JSON файлов.
Модель отвечает на аналитические вопросы локально, без облака.

Запуск:
    python3 analyst.py <путь_к_файлу> [модель]
    python3 analyst.py sample_data/server_logs.csv
    python3 analyst.py sample_data/user_funnel.json qwen2.5
"""

import json
import os
import sys
import urllib.request
import urllib.error

from data_loader import load_file, format_statistics, format_full_data
from prompts import ANALYST_SYSTEM, DATA_CONTEXT_TEMPLATE, WELCOME_TEMPLATE


OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3"


def build_context(filepath, data_type, data, summary):
    """Собирает контекст с данными для LLM."""
    stats_text = format_statistics(data_type.lower(), summary)
    full_text = format_full_data(data)

    count = summary.get("row_count") or summary.get("record_count", 0)
    if data_type == "CSV":
        desc = f"CSV файл, {count} строк, {len(summary['columns'])} колонок"
    else:
        desc = f"JSON файл, {count} записей, {len(summary['fields'])} полей"

    return DATA_CONTEXT_TEMPLATE.format(
        filename=os.path.basename(filepath),
        data_type=data_type,
        description=desc,
        statistics=stats_text,
        full_data=full_text,
    )


def query_streaming(messages, model):
    """Отправляет запрос к Ollama со стримингом ответа."""
    data = json.dumps({
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_ctx": 8192,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    full_response = ""
    with urllib.request.urlopen(req) as response:
        for line in response:
            if line:
                chunk_data = json.loads(line.decode("utf-8"))
                chunk = chunk_data.get("message", {}).get("content", "")
                print(chunk, end="", flush=True)
                full_response += chunk

    print("\n")
    return full_response


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 analyst.py <путь_к_файлу> [модель]")
        print()
        print("Примеры:")
        print("  python3 analyst.py sample_data/server_logs.csv")
        print("  python3 analyst.py sample_data/user_funnel.json qwen2.5")
        sys.exit(1)

    filepath = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL

    if not os.path.exists(filepath):
        print(f"Ошибка: файл не найден — {filepath}")
        sys.exit(1)

    # Загрузка данных
    print(f"Загрузка данных из {filepath}...")
    try:
        data_type, data, summary = load_file(filepath)
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        sys.exit(1)

    # Контекст для LLM
    data_context = build_context(filepath, data_type, data, summary)

    messages = [
        {"role": "system", "content": ANALYST_SYSTEM},
        {"role": "user", "content": data_context},
        {"role": "assistant", "content": "Данные загружены. Я готов отвечать на ваши вопросы об этих данных."},
    ]

    # Приветствие
    count = summary.get("row_count") or summary.get("record_count", 0)
    print(WELCOME_TEMPLATE.format(
        model=model,
        filename=os.path.basename(filepath),
        data_type=data_type,
        record_count=count,
    ))

    # Интерактивный цикл
    while True:
        try:
            user_input = input("Ваш вопрос: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nДо свидания!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("выход", "exit", "quit", "q"):
            print("До свидания!")
            break

        messages.append({"role": "user", "content": user_input})

        print("Аналитик: ", end="", flush=True)

        try:
            response = query_streaming(messages, model)
            messages.append({"role": "assistant", "content": response})
        except urllib.error.URLError:
            print("Ошибка: не удалось подключиться к Ollama. Убедитесь, что запущена: ollama serve")
            messages.pop()
        except Exception as e:
            print(f"Ошибка: {e}")
            messages.pop()


if __name__ == "__main__":
    main()
