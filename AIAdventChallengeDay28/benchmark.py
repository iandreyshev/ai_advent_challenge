#!/usr/bin/env python3
"""
Бенчмарк для сравнения оптимизаций LLM.

Измеряет:
- Время ответа
- Качество извлечения данных (сравнение с эталоном)
- Консистентность ответов при повторных запросах
- Влияние параметров на результат

Запуск:
    python3 benchmark.py [модель]
"""

import json
import re
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

from prompts import (
    BASIC_SYSTEM, OPTIMIZED_SYSTEM,
    EXTRACTION_BASIC, EXTRACTION_STRUCTURED, EXTRACTION_COT,
    PARAM_CONFIGS
)


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5"


@dataclass
class BenchmarkResult:
    """Результат одного теста."""
    config_name: str
    prompt_type: str
    response_time: float
    response_length: int
    extracted_fields: int
    json_valid: bool
    consistency_score: float


# Эталонные данные для проверки качества извлечения
TEST_CASES = [
    {
        "text": """iPhone 15 Pro Max 256GB в цвете титановый чёрный.
        Процессор A17 Pro, камера 48 Мп, экран 6.7" Super Retina XDR.
        Цена: 149 990 руб. В наличии на складе.""",
        "expected": {
            "название": "iPhone 15 Pro Max 256GB",
            "цена": "149 990 руб.",
            "наличие": "в наличии"
        }
    },
    {
        "text": """Продаю MacBook Air M2 2023 года.
        8GB RAM, 512GB SSD. Цвет: серебристый.
        Идеальное состояние, в комплекте зарядка.
        Цена 95000₽, возможен торг.""",
        "expected": {
            "название": "MacBook Air M2",
            "цена": "95000",
            "наличие": "в наличии"
        }
    },
    {
        "text": """Кроссовки Adidas Ultraboost, размер 43.
        Б/у, в хорошем состоянии. Пробег около 100 км.
        Отдам за 3500.""",
        "expected": {
            "название": "Adidas Ultraboost",
            "цена": "3500",
            "категория": "обувь"
        }
    }
]


def query_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: str = "",
    options: dict | None = None
) -> tuple[str, float]:
    """Отправляет запрос к Ollama."""
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

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("response", ""), time.time() - start
    except Exception as e:
        return f"ERROR: {e}", 0.0


def extract_json_from_response(response: str) -> dict | None:
    """Извлекает JSON из ответа модели."""
    # Ищем JSON в тексте
    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Пробуем найти JSON с вложенными массивами
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


def calculate_extraction_score(extracted: dict | None, expected: dict) -> float:
    """Вычисляет оценку качества извлечения (0.0 - 1.0)."""
    if not extracted:
        return 0.0

    matches = 0
    total = len(expected)

    for key, expected_value in expected.items():
        if key in extracted:
            extracted_value = str(extracted[key]).lower()
            expected_lower = str(expected_value).lower()

            # Частичное совпадение
            if expected_lower in extracted_value or extracted_value in expected_lower:
                matches += 1
            # Числовое совпадение (для цен)
            elif re.search(r'\d+', expected_lower):
                expected_nums = re.findall(r'\d+', expected_lower)
                extracted_nums = re.findall(r'\d+', extracted_value)
                if set(expected_nums) & set(extracted_nums):
                    matches += 0.5

    return matches / total if total > 0 else 0.0


def run_consistency_test(
    prompt: str,
    model: str,
    system: str,
    options: dict,
    runs: int = 3
) -> tuple[list[str], float]:
    """Проверяет консистентность ответов при повторных запросах."""
    responses = []

    for _ in range(runs):
        response, _ = query_ollama(prompt, model, system, options)
        responses.append(response)

    # Вычисляем консистентность (насколько похожи ответы)
    if len(responses) < 2:
        return responses, 1.0

    # Простая метрика: доля общих слов
    def get_words(text: str) -> set:
        return set(re.findall(r'\w+', text.lower()))

    total_similarity = 0
    comparisons = 0

    for i in range(len(responses)):
        for j in range(i + 1, len(responses)):
            words1 = get_words(responses[i])
            words2 = get_words(responses[j])
            if words1 or words2:
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                total_similarity += intersection / union if union > 0 else 0
            comparisons += 1

    consistency = total_similarity / comparisons if comparisons > 0 else 1.0
    return responses, consistency


def run_benchmark(model: str = DEFAULT_MODEL) -> list[BenchmarkResult]:
    """Запускает полный бенчмарк."""
    results = []

    prompt_configs = [
        ("basic", EXTRACTION_BASIC, BASIC_SYSTEM),
        ("structured", EXTRACTION_STRUCTURED, OPTIMIZED_SYSTEM),
        ("cot", EXTRACTION_COT, OPTIMIZED_SYSTEM),
    ]

    param_configs = [
        ("precise", {"temperature": 0.1, "top_p": 0.5, "num_predict": 300}),
        ("balanced", {"temperature": 0.5, "top_p": 0.9, "num_predict": 300}),
        ("creative", {"temperature": 0.9, "top_p": 0.95, "num_predict": 300}),
    ]

    print("\n" + "=" * 70)
    print(" ЗАПУСК БЕНЧМАРКА")
    print("=" * 70)

    total_tests = len(TEST_CASES) * len(prompt_configs) * len(param_configs)
    current = 0

    for test_case in TEST_CASES:
        text = test_case["text"]
        expected = test_case["expected"]

        for prompt_name, prompt_template, system in prompt_configs:
            prompt = prompt_template.format(text=text)

            for config_name, options in param_configs:
                current += 1
                print(f"\r[{current}/{total_tests}] {prompt_name} + {config_name}...", end="", flush=True)

                # Запрос
                response, elapsed = query_ollama(prompt, model, system, options)

                # Анализ ответа
                extracted_json = extract_json_from_response(response)
                extraction_score = calculate_extraction_score(extracted_json, expected)

                # Тест консистентности (только для precise конфигурации)
                consistency = 1.0
                if config_name == "precise":
                    _, consistency = run_consistency_test(prompt, model, system, options, runs=2)

                result = BenchmarkResult(
                    config_name=config_name,
                    prompt_type=prompt_name,
                    response_time=elapsed,
                    response_length=len(response),
                    extracted_fields=len(extracted_json) if extracted_json else 0,
                    json_valid=extracted_json is not None,
                    consistency_score=consistency
                )
                results.append(result)

    print("\n")
    return results


def print_benchmark_summary(results: list[BenchmarkResult]) -> None:
    """Выводит сводку результатов бенчмарка."""
    print("\n" + "=" * 70)
    print(" РЕЗУЛЬТАТЫ БЕНЧМАРКА")
    print("=" * 70)

    # Группировка по типу промпта
    by_prompt = {}
    for r in results:
        if r.prompt_type not in by_prompt:
            by_prompt[r.prompt_type] = []
        by_prompt[r.prompt_type].append(r)

    print("\n📊 ПО ТИПУ ПРОМПТА:")
    print("-" * 50)

    for prompt_type, prompt_results in by_prompt.items():
        avg_time = sum(r.response_time for r in prompt_results) / len(prompt_results)
        json_rate = sum(1 for r in prompt_results if r.json_valid) / len(prompt_results) * 100
        avg_fields = sum(r.extracted_fields for r in prompt_results) / len(prompt_results)

        print(f"\n  {prompt_type.upper()}:")
        print(f"    Среднее время: {avg_time:.2f}с")
        print(f"    Валидный JSON: {json_rate:.0f}%")
        print(f"    Ср. полей в ответе: {avg_fields:.1f}")

    # Группировка по конфигурации параметров
    by_config = {}
    for r in results:
        if r.config_name not in by_config:
            by_config[r.config_name] = []
        by_config[r.config_name].append(r)

    print("\n\n📊 ПО КОНФИГУРАЦИИ ПАРАМЕТРОВ:")
    print("-" * 50)

    for config_name, config_results in by_config.items():
        avg_time = sum(r.response_time for r in config_results) / len(config_results)
        json_rate = sum(1 for r in config_results if r.json_valid) / len(config_results) * 100
        avg_consistency = sum(r.consistency_score for r in config_results) / len(config_results)

        print(f"\n  {config_name.upper()}:")
        print(f"    Среднее время: {avg_time:.2f}с")
        print(f"    Валидный JSON: {json_rate:.0f}%")
        print(f"    Консистентность: {avg_consistency:.0%}")

    # Лучшие комбинации
    print("\n\n🏆 ЛУЧШИЕ КОМБИНАЦИИ:")
    print("-" * 50)

    # Лучшая по скорости
    fastest = min(results, key=lambda r: r.response_time)
    print(f"\n  Самый быстрый: {fastest.prompt_type} + {fastest.config_name} ({fastest.response_time:.2f}с)")

    # Лучшая по качеству JSON
    valid_results = [r for r in results if r.json_valid]
    if valid_results:
        best_quality = max(valid_results, key=lambda r: r.extracted_fields)
        print(f"  Лучшее качество: {best_quality.prompt_type} + {best_quality.config_name} ({best_quality.extracted_fields} полей)")

    # Рекомендации
    print("\n\n💡 РЕКОМЕНДАЦИИ:")
    print("-" * 50)

    # Анализируем результаты для рекомендаций
    structured_results = [r for r in results if r.prompt_type == "structured"]
    precise_results = [r for r in results if r.config_name == "precise"]

    if structured_results:
        struct_json_rate = sum(1 for r in structured_results if r.json_valid) / len(structured_results)
        if struct_json_rate > 0.7:
            print("\n  ✅ Структурированные промпты дают более предсказуемый JSON")

    if precise_results:
        precise_consistency = sum(r.consistency_score for r in precise_results) / len(precise_results)
        if precise_consistency > 0.8:
            print("  ✅ Низкая температура (precise) обеспечивает стабильные ответы")

    print("\n  📌 Для задач извлечения данных рекомендуется:")
    print("     - Использовать структурированные промпты с примером формата")
    print("     - Установить temperature=0.1-0.3 для точности")
    print("     - Использовать Chain-of-Thought для сложных текстов")


def main():
    """Главная функция."""
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL

    print(f"🔬 Бенчмарк оптимизации LLM")
    print(f"   Модель: {model}")

    # Проверка Ollama
    response, _ = query_ollama("test", model, options={"num_predict": 1})
    if "ERROR" in response:
        print(f"\n❌ {response}")
        print("\nУбедитесь, что Ollama запущена: ollama serve")
        return

    results = run_benchmark(model)
    print_benchmark_summary(results)

    print("\n" + "=" * 70)
    print(" Бенчмарк завершён")
    print("=" * 70)


if __name__ == "__main__":
    main()
