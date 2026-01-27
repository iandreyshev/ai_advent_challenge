"""Система памяти: сохранение и загрузка фактов между сессиями."""

import json
import os
from datetime import datetime


DEFAULT_MEMORY_PATH = os.path.join(os.path.dirname(__file__), "memory.json")
MAX_FACTS = 50


def load_memory(path=None):
    """Загружает факты из JSON файла."""
    filepath = path or DEFAULT_MEMORY_PATH

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            facts = json.load(f)
        if isinstance(facts, list):
            return facts
        return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Предупреждение: файл памяти повреждён, начинаю с чистой памяти.")
        return []


def save_memory(facts, path=None):
    """Сохраняет факты в JSON файл."""
    filepath = path or DEFAULT_MEMORY_PATH

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)


def add_fact(fact_text, source="manual", facts=None, path=None):
    """
    Добавляет факт в память.
    Возвращает (True, facts) если добавлен, (False, facts) если дубликат.
    """
    if facts is None:
        facts = load_memory(path)

    # Проверка дубликатов (без учёта регистра)
    fact_lower = fact_text.lower().strip()
    for existing in facts:
        if existing.get("fact", "").lower().strip() == fact_lower:
            return False, facts

    new_fact = {
        "fact": fact_text.strip(),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": source,
    }
    facts.append(new_fact)

    # Лимит: удаляем самые старые
    if len(facts) > MAX_FACTS:
        facts = facts[-MAX_FACTS:]

    save_memory(facts, path)
    return True, facts


def clear_memory(path=None):
    """Очищает всю память."""
    save_memory([], path)


def format_memory_for_prompt(facts):
    """Форматирует факты для системного промпта."""
    if not facts:
        return "Пока нет сохранённых фактов."

    lines = []
    for item in facts:
        fact = item.get("fact", "")
        date = item.get("date", "")
        lines.append(f"- {fact} ({date})")

    return "\n".join(lines)


def display_memory(facts):
    """Выводит память в терминал."""
    sep = "=" * 55
    print(f"\n{sep}")
    print("  Память агента")
    print(sep)

    if not facts:
        print("  Память пуста.")
    else:
        for i, item in enumerate(facts, 1):
            fact = item.get("fact", "")
            date = item.get("date", "")
            source = item.get("source", "")
            tag = " [авто]" if source == "auto" else ""
            print(f"  {i}. {fact} ({date}){tag}")

    print(sep)
    print()
