#!/usr/bin/env python3
"""
День 30: Персональный AI-агент.

Агент с персонализацией: загружает профиль пользователя из YAML,
подстраивает поведение, запоминает факты между сессиями.

Запуск:
    python3 agent.py
    python3 agent.py --profile my_profile.yaml
    python3 agent.py --model llama3
    python3 agent.py --no-auto-memory
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

from user_profile import load_profile, build_system_prompt, display_profile
from memory import (
    load_memory, add_fact, clear_memory,
    format_memory_for_prompt, display_memory,
)
from prompts import WELCOME_TEMPLATE, FACT_EXTRACTION_PROMPT, FACT_REPHRASE_PROMPT


OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5"


def query_streaming(messages, model):
    """Отправляет запрос к Ollama со стримингом ответа."""
    data = json.dumps({
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.7,
            "num_ctx": 4096,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_CHAT_URL,
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


def _query_generate(prompt, model, temperature=0.1, num_predict=60):
    """Отправляет короткий запрос к Ollama (без стриминга)."""
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_GENERATE_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))
        return result.get("response", "").strip().strip('"\'')


def try_extract_fact(user_message, model, user_name):
    """Пробует извлечь важный факт из сообщения пользователя (от третьего лица)."""
    prompt = FACT_EXTRACTION_PROMPT.format(message=user_message, user_name=user_name)

    try:
        fact = _query_generate(prompt, model)
        if fact and fact.lower() != "нет" and len(fact) > 3 and len(fact) < 200:
            return fact
    except Exception:
        pass

    return None


def rephrase_fact(fact_text, model, user_name):
    """Перефразирует факт от третьего лица через LLM."""
    prompt = FACT_REPHRASE_PROMPT.format(fact=fact_text, user_name=user_name)

    try:
        result = _query_generate(prompt, model)
        if result and len(result) > 3 and len(result) < 200:
            return result
    except Exception:
        pass

    return fact_text  # Если LLM недоступна, сохраняем как есть


def handle_command(cmd, profile, messages, memory_facts, model_holder, auto_memory):
    """Обработка команд, начинающихся с /."""
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if command == "/profile":
        display_profile(profile)

    elif command == "/memory":
        display_memory(memory_facts)

    elif command == "/remember":
        if not arg:
            print("Использование: /remember <факт>")
            return
        user_name = profile.get("name", "Пользователь")
        rephrased = rephrase_fact(arg, model_holder[0], user_name)
        added, memory_facts[:] = add_fact(rephrased, source="manual", facts=memory_facts)
        if added:
            print(f"  Запомнил: {rephrased}")
            _rebuild_system(messages, profile, memory_facts)
        else:
            print("  Этот факт уже сохранён.")

    elif command == "/forget":
        clear_memory()
        memory_facts.clear()
        print("  Память очищена.")
        _rebuild_system(messages, profile, memory_facts)

    elif command == "/clear":
        messages[:] = [messages[0]]
        print("  История чата очищена.")

    elif command == "/model":
        if not arg:
            print(f"  Текущая модель: {model_holder[0]}")
            print("  Использование: /model <имя>")
            return
        model_holder[0] = arg
        print(f"  Модель изменена на: {arg}")

    elif command == "/help":
        _print_help()

    else:
        print(f"  Неизвестная команда: {command}")
        print("  Введите /help для списка команд.")


def _rebuild_system(messages, profile, memory_facts):
    """Пересобирает системный промпт с обновлённой памятью."""
    memory_text = format_memory_for_prompt(memory_facts)
    system_prompt = build_system_prompt(profile, memory_text)
    messages[0] = {"role": "system", "content": system_prompt}


def _print_help():
    """Выводит справку по командам."""
    sep = "=" * 55
    print(f"\n{sep}")
    print("  Команды:")
    print(f"{sep}")
    print("  /profile          — показать профиль")
    print("  /remember <факт>  — запомнить факт")
    print("  /memory           — показать память")
    print("  /forget           — очистить память")
    print("  /clear            — очистить историю чата")
    print("  /model <имя>      — сменить модель")
    print("  /help             — эта справка")
    print("  exit / quit       — выход")
    print(sep)
    print()


def main():
    parser = argparse.ArgumentParser(description="Персональный AI-агент")
    parser.add_argument("--profile", default=None, help="Путь к файлу профиля (YAML)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Модель Ollama")
    parser.add_argument(
        "--no-auto-memory", action="store_true",
        help="Отключить автоматическое запоминание фактов",
    )
    args = parser.parse_args()

    # Загрузка профиля и памяти
    profile = load_profile(args.profile)
    memory_facts = load_memory()
    memory_text = format_memory_for_prompt(memory_facts)

    # Системный промпт с профилем и памятью
    system_prompt = build_system_prompt(profile, memory_text)

    messages = [{"role": "system", "content": system_prompt}]

    # Используем list для мутабельности в handle_command
    model_holder = [args.model]
    auto_memory = not args.no_auto_memory

    # Приветствие
    agent = profile.get("agent", {})
    user_name = profile.get("name", "Пользователь")

    print(WELCOME_TEMPLATE.format(
        model=model_holder[0],
        user_name=user_name,
        user_role=profile.get("role", "—"),
        agent_name=agent.get("name", "Ассистент"),
    ))

    if memory_facts:
        print(f"  Загружено фактов из памяти: {len(memory_facts)}")
        print()

    # Приветствие агента
    greeting = agent.get("greeting", "Привет! Чем могу помочь?")
    greeting = greeting.replace("{user_name}", user_name)
    print(f"{agent.get('name', 'Ассистент')}: {greeting}\n")

    # Интерактивный цикл
    while True:
        try:
            user_input = input("Вы: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nДо свидания!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("выход", "exit", "quit", "q"):
            print("До свидания!")
            break

        # Команды
        if user_input.startswith("/"):
            handle_command(
                user_input, profile, messages,
                memory_facts, model_holder, auto_memory,
            )
            continue

        # Обычное сообщение
        messages.append({"role": "user", "content": user_input})

        agent_name = agent.get("name", "Ассистент")
        print(f"{agent_name}: ", end="", flush=True)

        try:
            response = query_streaming(messages, model_holder[0])
            messages.append({"role": "assistant", "content": response})

            # Авто-извлечение фактов
            if auto_memory:
                fact = try_extract_fact(user_input, model_holder[0], user_name)
                if fact:
                    added, memory_facts[:] = add_fact(
                        fact, source="auto", facts=memory_facts,
                    )
                    if added:
                        print(f"  [запомнил: {fact}]")
                        _rebuild_system(messages, profile, memory_facts)

        except urllib.error.URLError:
            print("Ошибка: не удалось подключиться к Ollama.")
            print("Убедитесь, что запущена: ollama serve")
            messages.pop()
        except Exception as e:
            print(f"Ошибка: {e}")
            messages.pop()


if __name__ == "__main__":
    main()
