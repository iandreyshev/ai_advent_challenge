#!/usr/bin/env python3
"""
Демонстрационный скрипт для God Agent.
Показывает возможности агента без необходимости интерактивного ввода.
"""

import sys
from tools import (
    OllamaClient,
    Memory,
    Profile,
    DataAnalytics,
    take_screenshot,
    launch_workspace_apps,
    VOICE_AVAILABLE,
)


def demo_profile():
    """Демонстрация профиля."""
    print("\n" + "=" * 60)
    print("📋 ДЕМО: Профиль пользователя")
    print("=" * 60)

    profile = Profile("profile.yaml")
    profile.display()


def demo_memory():
    """Демонстрация памяти."""
    print("\n" + "=" * 60)
    print("💾 ДЕМО: Система памяти")
    print("=" * 60)

    memory = Memory(memory_file="demo_memory.json")
    memory.clear()

    print("\nДобавляю тестовые факты...")
    memory.add_fact("Иван предпочитает Swift вместо Objective-C", source="manual")
    memory.add_fact("Иван работает над AI Advent Challenge", source="auto")
    memory.add_fact("Иван использует VS Code и Xcode", source="manual")

    print()
    memory.display()

    # Очистка
    import os
    if os.path.exists("demo_memory.json"):
        os.remove("demo_memory.json")


def demo_analytics():
    """Демонстрация аналитики данных."""
    print("\n" + "=" * 60)
    print("📊 ДЕМО: Анализ данных")
    print("=" * 60)

    # Создаём тестовые данные
    import json
    import os

    test_data = [
        {"name": "Alice", "age": 30, "city": "Moscow", "score": 95},
        {"name": "Bob", "age": 25, "city": "Moscow", "score": 87},
        {"name": "Charlie", "age": 35, "city": "SPb", "score": 92},
        {"name": "Diana", "age": 28, "city": "Moscow", "score": 88},
    ]

    test_file = "demo_data.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    analytics = DataAnalytics()
    success, message = analytics.load_file(test_file)

    print(f"\n{message}")
    if success:
        print("\n" + analytics.get_summary_text())

    # Очистка
    if os.path.exists(test_file):
        os.remove(test_file)


def demo_tools():
    """Демонстрация инструментов."""
    print("\n" + "=" * 60)
    print("🛠  ДЕМО: Инструменты")
    print("=" * 60)

    print("\nДоступные инструменты:")
    print("  ✅ Скриншоты экрана (take_screenshot)")
    print("  ✅ Запуск приложений (launch_workspace_apps)")
    print(f"  {'✅' if VOICE_AVAILABLE else '⚠️ '} Голосовое управление (VoiceRecognition)")

    if not VOICE_AVAILABLE:
        print("\n⚠️  Голосовое управление недоступно.")
        print("   Установите: pip3 install --break-system-packages SpeechRecognition PyAudio")


def demo_llm():
    """Демонстрация LLM клиента."""
    print("\n" + "=" * 60)
    print("🤖 ДЕМО: LLM клиент")
    print("=" * 60)

    try:
        llm = OllamaClient(model="qwen2.5")
        print(f"\nМодель: {llm.model}")
        print(f"URL: {llm.chat_url}")
        print("\n✅ LLM клиент готов к работе")
        print("   (для реального теста нужна запущенная Ollama: ollama serve)")

    except Exception as e:
        print(f"\n⚠️  Ошибка: {e}")


def main():
    """Запускает все демонстрации."""
    print("=" * 60)
    print("⚡️ GOD AGENT — ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ")
    print("=" * 60)

    demos = [
        ("Профиль", demo_profile),
        ("Память", demo_memory),
        ("Аналитика", demo_analytics),
        ("Инструменты", demo_tools),
        ("LLM", demo_llm),
    ]

    for name, func in demos:
        try:
            func()
        except Exception as e:
            print(f"\n❌ Ошибка в демо '{name}': {e}")

    print("\n" + "=" * 60)
    print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)
    print("\nДля запуска агента:")
    print("  python3 god_agent.py          # текстовый режим")
    print("  python3 god_agent.py --voice  # голосовой режим")
    print()


if __name__ == "__main__":
    main()
