#!/usr/bin/env python3
"""
День 28: Оптимизация и адаптация локальной LLM

Демонстрация влияния параметров модели и prompt-шаблонов на качество ответов.
Использует Ollama для локального запуска LLM.

Параметры для оптимизации:
- temperature: контролирует случайность (0.0 = детерминированно, 1.0 = креативно)
- top_p: nucleus sampling (вероятностный порог для выбора токенов)
- num_predict (max_tokens): максимальная длина ответа
- num_ctx: размер контекстного окна
- repeat_penalty: штраф за повторения

Запуск:
    python3 optimize_llm.py [режим]

Режимы:
    demo      - интерактивная демонстрация (по умолчанию)
    compare   - сравнение параметров
    prompts   - сравнение prompt-шаблонов
"""

import json
import time
import urllib.request
import urllib.error
from typing import Any

from prompts import (
    BASIC_SYSTEM, OPTIMIZED_SYSTEM,
    EXTRACTION_BASIC, EXTRACTION_STRUCTURED, EXTRACTION_COT,
    CLASSIFY_BASIC, CLASSIFY_STRUCTURED,
    TEST_PRODUCTS, TEST_REVIEWS,
    PARAM_CONFIGS, CONTEXT_CONFIGS
)


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5"


def query_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: str = "",
    options: dict | None = None
) -> tuple[str, float]:
    """Отправляет запрос к Ollama и возвращает ответ с временем выполнения."""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options or {}
    }

    if system:
        payload["system"] = system

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    start_time = time.time()

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            elapsed = time.time() - start_time
            return result.get("response", ""), elapsed
    except urllib.error.URLError as e:
        return f"Ошибка подключения к Ollama: {e}", 0.0
    except Exception as e:
        return f"Ошибка: {e}", 0.0


def print_header(title: str) -> None:
    """Выводит заголовок секции."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_result(label: str, response: str, elapsed: float) -> None:
    """Выводит результат запроса."""
    print(f"\n--- {label} (время: {elapsed:.2f}с) ---")
    print(response[:500] + "..." if len(response) > 500 else response)


def demo_temperature_impact(model: str = DEFAULT_MODEL) -> None:
    """Демонстрация влияния температуры на ответы."""
    print_header("ВЛИЯНИЕ ТЕМПЕРАТУРЫ НА ОТВЕТЫ")

    prompt = "Придумай название для стартапа, который делает приложение для учёта расходов."

    temperatures = [0.0, 0.3, 0.7, 1.0]

    print(f"\nПромпт: {prompt}\n")

    for temp in temperatures:
        options = {"temperature": temp, "num_predict": 100}
        response, elapsed = query_ollama(prompt, model, options=options)
        print(f"\n[temperature={temp}] ({elapsed:.2f}с)")
        print(f"  → {response.strip()}")


def demo_context_window(model: str = DEFAULT_MODEL) -> None:
    """Демонстрация влияния размера контекстного окна."""
    print_header("ВЛИЯНИЕ РАЗМЕРА КОНТЕКСТНОГО ОКНА")

    # Длинный контекст для демонстрации
    long_context = """
    История компании:

    2020: Основание компании тремя инженерами из Яндекса.
    2021: Первый раунд инвестиций на $2M от венчурного фонда.
    2022: Запуск MVP продукта, первые 1000 пользователей.
    2023: Серия A на $15M, выход на рынки СНГ.
    2024: 100,000 активных пользователей, партнёрство с банками.
    2025: Планируется IPO на Московской бирже.

    Ключевые продукты: мобильное приложение, API для B2B, аналитическая платформа.
    Команда: 50 человек, офисы в Москве и Казани.
    """

    prompt = f"{long_context}\n\nВопрос: Когда компания планирует IPO и на какой бирже?"

    for config_name, config in CONTEXT_CONFIGS.items():
        options = {
            "num_ctx": config["num_ctx"],
            "temperature": 0.1,
            "num_predict": 100
        }
        response, elapsed = query_ollama(prompt, model, options=options)
        print(f"\n[{config_name}: num_ctx={config['num_ctx']}] ({elapsed:.2f}с)")
        print(f"  {config['description']}")
        print(f"  → {response.strip()}")


def compare_param_configs(model: str = DEFAULT_MODEL) -> None:
    """Сравнение предустановленных конфигураций параметров."""
    print_header("СРАВНЕНИЕ КОНФИГУРАЦИЙ ПАРАМЕТРОВ")

    test_text = TEST_PRODUCTS[0]
    prompt = EXTRACTION_STRUCTURED.format(text=test_text)

    print(f"\nТестовый текст:\n{test_text}\n")

    for config_name, config in PARAM_CONFIGS.items():
        options = {
            "temperature": config["temperature"],
            "top_p": config["top_p"],
            "num_predict": config["num_predict"]
        }

        response, elapsed = query_ollama(
            prompt, model,
            system=OPTIMIZED_SYSTEM,
            options=options
        )

        print(f"\n[{config_name.upper()}] - {config['description']}")
        print(f"  temperature={config['temperature']}, top_p={config['top_p']}")
        print(f"  Время: {elapsed:.2f}с")
        print(f"  Ответ:\n{response.strip()}")


def compare_prompts(model: str = DEFAULT_MODEL) -> None:
    """Сравнение разных prompt-шаблонов для одной задачи."""
    print_header("СРАВНЕНИЕ PROMPT-ШАБЛОНОВ")

    test_text = TEST_PRODUCTS[1]  # Менее структурированное объявление

    print(f"\nТестовый текст:\n{test_text}\n")

    prompts_to_test = [
        ("Базовый промпт", EXTRACTION_BASIC, BASIC_SYSTEM),
        ("Структурированный промпт", EXTRACTION_STRUCTURED, OPTIMIZED_SYSTEM),
        ("Chain-of-Thought промпт", EXTRACTION_COT, OPTIMIZED_SYSTEM),
    ]

    options = {"temperature": 0.1, "num_predict": 400}

    for name, prompt_template, system in prompts_to_test:
        prompt = prompt_template.format(text=test_text)
        response, elapsed = query_ollama(prompt, model, system=system, options=options)
        print_result(name, response, elapsed)


def compare_classification_prompts(model: str = DEFAULT_MODEL) -> None:
    """Сравнение промптов для классификации тональности."""
    print_header("КЛАССИФИКАЦИЯ ТОНАЛЬНОСТИ: БАЗОВЫЙ vs СТРУКТУРИРОВАННЫЙ")

    options = {"temperature": 0.1, "num_predict": 200}

    for i, review in enumerate(TEST_REVIEWS, 1):
        print(f"\n--- Отзыв {i} ---")
        print(f"Текст: {review}\n")

        # Базовый промпт
        response1, t1 = query_ollama(
            CLASSIFY_BASIC.format(text=review),
            model, options=options
        )
        print(f"[Базовый] ({t1:.2f}с): {response1.strip()}")

        # Структурированный промпт
        response2, t2 = query_ollama(
            CLASSIFY_STRUCTURED.format(text=review),
            model, system=OPTIMIZED_SYSTEM, options=options
        )
        print(f"[Структурированный] ({t2:.2f}с):\n{response2.strip()}")


def print_menu(model: str) -> None:
    """Выводит меню демонстраций."""
    print(f"""
Модель: {model}

Доступные демонстрации:
  1. Влияние температуры на креативность
  2. Влияние размера контекстного окна
  3. Сравнение конфигураций параметров
  4. Сравнение prompt-шаблонов (извлечение данных)
  5. Сравнение prompt-шаблонов (классификация)
  6. Запустить все демонстрации
  0. Выход
""")


def interactive_demo(model: str = DEFAULT_MODEL) -> None:
    """Интерактивная демонстрация оптимизации."""
    print_header("ИНТЕРАКТИВНАЯ ДЕМОНСТРАЦИЯ ОПТИМИЗАЦИИ LLM")
    print_menu(model)

    while True:
        try:
            choice = input("\nВыберите демонстрацию (0-6): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nВыход...")
            break

        if choice == "0":
            print("До свидания!")
            break
        elif choice == "1":
            demo_temperature_impact(model)
            print_menu(model)
        elif choice == "2":
            demo_context_window(model)
            print_menu(model)
        elif choice == "3":
            compare_param_configs(model)
            print_menu(model)
        elif choice == "4":
            compare_prompts(model)
            print_menu(model)
        elif choice == "5":
            compare_classification_prompts(model)
            print_menu(model)
        elif choice == "6":
            demo_temperature_impact(model)
            demo_context_window(model)
            compare_param_configs(model)
            compare_prompts(model)
            compare_classification_prompts(model)
            print_menu(model)
        else:
            print("Неверный выбор. Введите число от 0 до 6.")


def main():
    """Главная функция."""
    import sys

    model = DEFAULT_MODEL
    mode = "demo"

    # Парсинг аргументов
    for arg in sys.argv[1:]:
        if arg in ("demo", "compare", "prompts", "all"):
            mode = arg
        elif not arg.startswith("-"):
            model = arg

    print(f"День 28: Оптимизация локальной LLM")
    print(f"Модель: {model}")

    # Проверка доступности Ollama
    try:
        response, _ = query_ollama("test", model, options={"num_predict": 1})
        if "Ошибка" in response:
            print(f"\n{response}")
            print("\nУбедитесь, что Ollama запущена: ollama serve")
            print(f"И модель загружена: ollama pull {model}")
            return
    except Exception as e:
        print(f"Ошибка подключения к Ollama: {e}")
        return

    if mode == "demo":
        interactive_demo(model)
    elif mode == "compare":
        compare_param_configs(model)
    elif mode == "prompts":
        compare_prompts(model)
        compare_classification_prompts(model)
    elif mode == "all":
        demo_temperature_impact(model)
        demo_context_window(model)
        compare_param_configs(model)
        compare_prompts(model)
        compare_classification_prompts(model)


if __name__ == "__main__":
    main()
