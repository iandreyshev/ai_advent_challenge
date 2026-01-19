#!/usr/bin/env python3
"""Простой консольный чат с Ollama (без внешних зависимостей)."""

import json
import urllib.request
import urllib.error


def chat(model: str = "qwen2.5"):
    """Запуск чата с локальной моделью Ollama."""
    url = "http://localhost:11434/api/chat"

    # Системный промпт для ответов на русском языке
    messages = [{
        "role": "system",
        "content": "Ты — полезный ассистент. Всегда отвечай только на русском языке. Не смешивай языки."
    }]

    print(f"Чат с моделью {model}. Введите 'выход' для завершения.\n")

    while True:
        try:
            user_input = input("Вы: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nДо свидания!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("выход", "exit", "quit"):
            print("До свидания!")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            data = json.dumps({
                "model": model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": 0.3}
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )

            print("Ассистент: ", end="", flush=True)

            full_response = ""
            with urllib.request.urlopen(req) as response:
                for line in response:
                    if line:
                        chunk_data = json.loads(line.decode("utf-8"))
                        chunk = chunk_data.get("message", {}).get("content", "")
                        print(chunk, end="", flush=True)
                        full_response += chunk

            print("\n")
            messages.append({"role": "assistant", "content": full_response})

        except urllib.error.URLError:
            print("Ошибка: Не удалось подключиться к Ollama. Убедитесь, что Ollama запущена.")
            messages.pop()
        except Exception as e:
            print(f"Ошибка: {e}")
            messages.pop()


if __name__ == "__main__":
    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5"
    chat(model)
