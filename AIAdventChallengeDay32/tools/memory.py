"""Система персистентной памяти агента."""

import json
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class Memory:
    """Управление памятью агента между сессиями."""

    def __init__(self, memory_file: str = "memory.json", max_facts: int = 100):
        self.memory_file = memory_file
        self.max_facts = max_facts
        self.facts: List[Dict[str, str]] = []
        self.load()

    def load(self) -> None:
        """Загружает факты из файла."""
        if not os.path.exists(self.memory_file):
            self.facts = []
            return

        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.facts = data
                else:
                    self.facts = []
        except (json.JSONDecodeError, IOError):
            print("⚠️  Не удалось загрузить память, начинаю с чистой памяти.")
            self.facts = []

    def save(self) -> None:
        """Сохраняет факты в файл."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.facts, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"⚠️  Не удалось сохранить память: {e}")

    def add_fact(self, fact_text: str, source: str = "manual") -> bool:
        """
        Добавляет факт в память.
        Возвращает True если добавлен, False если дубликат.
        """
        fact_lower = fact_text.lower().strip()

        # Проверка дубликатов
        for existing in self.facts:
            if existing.get("fact", "").lower().strip() == fact_lower:
                return False

        new_fact = {
            "fact": fact_text.strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": source,
        }
        self.facts.append(new_fact)

        # Ограничение количества фактов
        if len(self.facts) > self.max_facts:
            self.facts = self.facts[-self.max_facts:]

        self.save()
        return True

    def clear(self) -> None:
        """Очищает всю память."""
        self.facts = []
        self.save()

    def format_for_prompt(self) -> str:
        """Форматирует факты для системного промпта."""
        if not self.facts:
            return "Пока нет сохранённых фактов."

        lines = []
        for item in self.facts:
            fact = item.get("fact", "")
            date = item.get("date", "")
            lines.append(f"- {fact} ({date})")

        return "\n".join(lines)

    def display(self) -> None:
        """Выводит память в консоль."""
        sep = "=" * 60
        print(f"\n{sep}")
        print("💾 ПАМЯТЬ АГЕНТА")
        print(sep)

        if not self.facts:
            print("Память пуста.")
        else:
            for i, item in enumerate(self.facts, 1):
                fact = item.get("fact", "")
                date = item.get("date", "")
                source = item.get("source", "")
                tag = " [авто]" if source == "auto" else ""
                print(f"{i:2}. {fact}")
                print(f"    ({date}){tag}")

        print(sep)
        print(f"Всего фактов: {len(self.facts)}/{self.max_facts}")
        print(sep)

    def __len__(self) -> int:
        """Возвращает количество фактов."""
        return len(self.facts)
