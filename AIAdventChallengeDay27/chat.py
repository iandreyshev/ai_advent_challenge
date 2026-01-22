#!/usr/bin/env python3
"""
Консольный чат с удалённой Ollama на VPS.
"""

import argparse
import os
from pathlib import Path
import requests
import sys


def load_env():
    """Загрузить переменные из .env файла."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


load_env()

DEFAULT_HOST = os.getenv("OLLAMA_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5")


def mask_url(url: str) -> str:
    """Замаскировать IP адрес в URL для вывода."""
    import re
    return re.sub(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "***.***.***.***", url)


def check_connection(base_url: str) -> bool:
    """Проверка доступности сервера."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def list_models(base_url: str) -> list[str]:
    """Получить список доступных моделей."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except requests.RequestException:
        pass
    return []


def chat(base_url: str, model: str, messages: list[dict]) -> str:
    """Отправить сообщение и получить ответ."""
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
            },
            timeout=120,
        )

        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "")
        else:
            return f"[Ошибка {response.status_code}]: {response.text}"

    except requests.Timeout:
        return "[Ошибка]: Превышено время ожидания ответа"
    except requests.RequestException as e:
        return f"[Ошибка соединения]: {e}"


def main():
    parser = argparse.ArgumentParser(description="Чат с удалённой Ollama")
    parser.add_argument("--host", default=DEFAULT_HOST, help="IP адрес сервера")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Порт Ollama")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Модель для общения")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    model = args.model

    print(f"Подключение к {mask_url(base_url)}...")

    if not check_connection(base_url):
        print(f"Не удалось подключиться к серверу {mask_url(base_url)}")
        print("Проверьте:")
        print("  1. Сервер запущен: ollama serve")
        print("  2. Порт открыт: sudo ufw allow 11434/tcp")
        print("  3. Ollama слушает 0.0.0.0: OLLAMA_HOST=0.0.0.0:11434")
        sys.exit(1)

    models = list_models(base_url)
    if models:
        print(f"Доступные модели: {', '.join(models)}")

    if model not in models and models:
        print(f"Модель '{model}' не найдена, использую '{models[0]}'")
        model = models[0]

    print(f"Модель: {model}")
    print("Команды: exit, clear, model <name>")
    print("-" * 40)

    messages = []

    try:
        while True:
            try:
                user_input = input("\nВы: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Команды
            if user_input.lower() in ("выход", "exit", "quit"):
                print("До свидания!")
                break

            if user_input.lower() == "clear":
                messages = []
                print("История очищена")
                continue

            if user_input.lower().startswith("model "):
                new_model = user_input[6:].strip()
                if new_model in models:
                    model = new_model
                    messages = []
                    print(f"Модель изменена на: {model}")
                else:
                    print(f"Модель не найдена. Доступные: {', '.join(models)}")
                continue

            # Добавляем сообщение пользователя
            messages.append({"role": "user", "content": user_input})

            print("\nАссистент: ", end="", flush=True)

            # Получаем ответ
            response = chat(base_url, model, messages)
            print(response)

            # Добавляем ответ в историю
            messages.append({"role": "assistant", "content": response})

    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")


if __name__ == "__main__":
    main()
