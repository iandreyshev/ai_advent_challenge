#!/usr/bin/env python3
"""
Тестовый скрипт для голосового агента
Симулирует голосовые запросы без использования микрофона
"""

import requests
import json
from typing import List, Tuple


class AgentTester:
    """Тестер для голосового агента"""

    def __init__(self, model: str = "qwen2.5", host: str = "localhost", port: int = 11434):
        self.model = model
        self.ollama_url = f"http://{host}:{port}/api/generate"

    def query_llm(self, text: str) -> str:
        """Отправляет текст в LLM и возвращает ответ"""
        try:
            payload = {
                "model": self.model,
                "prompt": text,
                "stream": False
            }

            response = requests.post(self.ollama_url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            return "❌ Не удалось подключиться к Ollama"
        except requests.exceptions.Timeout:
            return "❌ Время ожидания истекло"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def test_queries(self, queries: List[str]):
        """Тестирует список запросов"""
        print("=" * 60)
        print("🧪 ТЕСТИРОВАНИЕ ГОЛОСОВОГО АГЕНТА")
        print("=" * 60)
        print(f"Модель: {self.model}")
        print(f"Количество тестов: {len(queries)}")
        print("=" * 60)
        print()

        results = []

        for i, query in enumerate(queries, 1):
            print(f"📝 Тест {i}/{len(queries)}: {query}")
            print("🤖 Обработка...")

            response = self.query_llm(query)

            print("\n" + "-" * 60)
            print("💬 ОТВЕТ:")
            print("-" * 60)
            print(response)
            print("=" * 60)
            print()

            results.append((query, response))

        return results


def main():
    # Тестовые запросы из задания
    test_queries = [
        "Посчитай сколько будет пятнадцать умножить на семь",
        "Дай определение машинного обучения",
        "Расскажи короткий анекдот про программистов",
        "Какая столица Франции",
        "Как приготовить омлет",
        "Что такое искусственный интеллект",
        "Сколько планет в солнечной системе",
        "Переведи на английский: Привет, как дела"
    ]

    tester = AgentTester()
    results = tester.test_queries(test_queries)

    # Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"Всего запросов: {len(results)}")
    successful = sum(1 for _, r in results if not r.startswith("❌"))
    print(f"Успешных: {successful}")
    print(f"Неудачных: {len(results) - successful}")
    print("=" * 60)


if __name__ == "__main__":
    main()
