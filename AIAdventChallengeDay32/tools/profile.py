"""Управление профилем пользователя."""

import os
import yaml
from typing import Dict, Any, Optional


class Profile:
    """Загрузка и управление профилем пользователя."""

    DEFAULT_PROFILE = {
        "name": "Пользователь",
        "role": "не указана",
        "preferences": {
            "language": "русский",
            "style": "нейтральный",
            "detail_level": "средний",
        },
        "agent": {
            "name": "God Agent",
            "tone": "дружелюбный и профессиональный",
            "behavior": "отвечай чётко и по делу",
            "greeting": "Привет, {user_name}! Я твой универсальный ассистент. Чем могу помочь?",
        },
    }

    def __init__(self, profile_file: Optional[str] = None):
        self.profile_file = profile_file or "profile.yaml"
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Загружает профиль из YAML файла."""
        if not os.path.exists(self.profile_file):
            print(f"⚠️  Профиль не найден: {self.profile_file}")
            print("   Используется профиль по умолчанию.")
            self.data = self.DEFAULT_PROFILE.copy()
            return

        try:
            with open(self.profile_file, "r", encoding="utf-8") as f:
                user_data = yaml.safe_load(f) or {}
                self.data = self._deep_merge(self.DEFAULT_PROFILE, user_data)
                print(f"✅ Профиль загружен: {self.profile_file}")
        except yaml.YAMLError as e:
            print(f"⚠️  Ошибка чтения YAML: {e}")
            self.data = self.DEFAULT_PROFILE.copy()

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Рекурсивно объединяет словари."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение из профиля."""
        return self.data.get(key, default)

    def build_system_prompt(self, memory_text: str = "") -> str:
        """Создаёт системный промпт на основе профиля и памяти."""
        agent = self.data.get("agent", self.DEFAULT_PROFILE["agent"])
        user_name = self.data.get("name", "Пользователь")
        user_role = self.data.get("role", "не указана")

        prefs = self.data.get("preferences", {})
        habits = self.data.get("habits", {})
        context = self.data.get("context", {})

        # Формируем промпт
        parts = [
            f"Ты — {agent.get('name', 'God Agent')}, персональный AI-ассистент пользователя {user_name}.",
            f"Роль пользователя: {user_role}.",
            f"Тон общения: {agent.get('tone', 'дружелюбный')}.",
            f"Поведение: {agent.get('behavior', 'отвечай по делу')}.",
        ]

        # Предпочтения
        if prefs:
            parts.append("\nПредпочтения пользователя:")
            if prefs.get("language"):
                parts.append(f"- Язык: {prefs['language']}")
            if prefs.get("style"):
                parts.append(f"- Стиль: {prefs['style']}")
            if prefs.get("detail_level"):
                parts.append(f"- Детализация: {prefs['detail_level']}")

        # Привычки
        if habits:
            parts.append("\nПривычки:")
            for key, value in habits.items():
                if isinstance(value, list):
                    parts.append(f"- {key}: {', '.join(value)}")
                else:
                    parts.append(f"- {key}: {value}")

        # Контекст
        if context:
            parts.append("\nТекущий контекст:")
            for key, value in context.items():
                if isinstance(value, list):
                    parts.append(f"- {key}:")
                    for item in value:
                        parts.append(f"  • {item}")
                else:
                    parts.append(f"- {key}: {value}")

        # Память
        if memory_text and memory_text != "Пока нет сохранённых фактов.":
            parts.append("\nЗапомненные факты:")
            parts.append(memory_text)

        return "\n".join(parts)

    def display(self) -> None:
        """Выводит профиль в консоль."""
        sep = "=" * 60
        print(f"\n{sep}")
        print("👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ")
        print(sep)
        print(f"Имя:  {self.data.get('name', '—')}")
        print(f"Роль: {self.data.get('role', '—')}")

        prefs = self.data.get("preferences", {})
        if prefs:
            print("\nПредпочтения:")
            if prefs.get("style"):
                print(f"  Стиль: {prefs['style']}")
            if prefs.get("detail_level"):
                print(f"  Детализация: {prefs['detail_level']}")

        habits = self.data.get("habits", {})
        if habits:
            print("\nПривычки:")
            for key, value in list(habits.items())[:3]:
                if isinstance(value, list):
                    print(f"  {key}: {', '.join(value[:3])}")
                else:
                    print(f"  {key}: {value}")

        context = self.data.get("context", {})
        if context and context.get("current_projects"):
            print("\nТекущие проекты:")
            for proj in context["current_projects"][:3]:
                print(f"  • {proj}")

        agent = self.data.get("agent", {})
        print(f"\nАгент: {agent.get('name', '—')} ({agent.get('tone', '—')})")
        print(sep)
