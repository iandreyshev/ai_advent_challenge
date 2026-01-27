"""Загрузка и управление профилем пользователя."""

import os

import yaml

from prompts import AGENT_SYSTEM_TEMPLATE


DEFAULT_PROFILE_PATH = os.path.join(os.path.dirname(__file__), "profile.yaml")

DEFAULT_PROFILE = {
    "name": "Пользователь",
    "role": "не указана",
    "preferences": {
        "language": "русский",
        "style": "нейтральный",
        "detail_level": "средний",
        "topics": [],
    },
    "habits": {},
    "context": {},
    "agent": {
        "name": "Ассистент",
        "tone": "дружелюбный",
        "behavior": "отвечай кратко и по делу",
        "greeting": "Привет! Чем могу помочь?",
    },
}


def _deep_merge(base, override):
    """Рекурсивно объединяет override в base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_profile(path=None):
    """Загружает профиль из YAML файла."""
    filepath = path or DEFAULT_PROFILE_PATH

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        profile = _deep_merge(DEFAULT_PROFILE, data)
        print(f"Профиль загружен: {filepath}")
        return profile
    except FileNotFoundError:
        print(f"Файл профиля не найден: {filepath}")
        print("Используется профиль по умолчанию. Создайте profile.yaml для персонализации.")
        return DEFAULT_PROFILE.copy()
    except yaml.YAMLError as e:
        print(f"Ошибка чтения YAML: {e}")
        return DEFAULT_PROFILE.copy()


def _format_list(items):
    """Форматирует список как маркированный текст."""
    if not items:
        return "не указано"
    return "\n".join(f"  - {item}" for item in items)


def format_preferences(prefs):
    """Форматирует предпочтения для системного промпта."""
    if not prefs:
        return "Не указаны"

    lines = []
    if prefs.get("language"):
        lines.append(f"Язык: {prefs['language']}")
    if prefs.get("style"):
        lines.append(f"Стиль общения: {prefs['style']}")
    if prefs.get("detail_level"):
        lines.append(f"Уровень детализации: {prefs['detail_level']}")
    if prefs.get("topics"):
        lines.append(f"Интересные темы:\n{_format_list(prefs['topics'])}")

    return "\n".join(lines) if lines else "Не указаны"


def format_habits(habits):
    """Форматирует привычки для системного промпта."""
    if not habits:
        return "Не указаны"

    lines = []
    if habits.get("work_hours"):
        lines.append(f"Рабочие часы: {habits['work_hours']}")
    if habits.get("breaks"):
        lines.append(f"Перерывы: {habits['breaks']}")
    if habits.get("productivity"):
        lines.append(f"Продуктивность: {habits['productivity']}")
    if habits.get("tools"):
        lines.append(f"Инструменты:\n{_format_list(habits['tools'])}")

    # Произвольные ключи
    known_keys = {"work_hours", "breaks", "productivity", "tools"}
    for key, value in habits.items():
        if key not in known_keys:
            if isinstance(value, list):
                lines.append(f"{key}:\n{_format_list(value)}")
            else:
                lines.append(f"{key}: {value}")

    return "\n".join(lines) if lines else "Не указаны"


def format_context(ctx):
    """Форматирует контекст для системного промпта."""
    if not ctx:
        return "Не указан"

    lines = []
    if ctx.get("current_projects"):
        lines.append(f"Текущие проекты:\n{_format_list(ctx['current_projects'])}")
    if ctx.get("goals"):
        lines.append(f"Цели:\n{_format_list(ctx['goals'])}")
    if ctx.get("tech_stack"):
        lines.append(f"Технологии:\n{_format_list(ctx['tech_stack'])}")

    # Произвольные ключи
    known_keys = {"current_projects", "goals", "tech_stack"}
    for key, value in ctx.items():
        if key not in known_keys:
            if isinstance(value, list):
                lines.append(f"{key}:\n{_format_list(value)}")
            else:
                lines.append(f"{key}: {value}")

    return "\n".join(lines) if lines else "Не указан"


def build_system_prompt(profile, memory_text="Пока нет сохранённых фактов."):
    """Собирает полный системный промпт из профиля и памяти."""
    agent = profile.get("agent", DEFAULT_PROFILE["agent"])

    return AGENT_SYSTEM_TEMPLATE.format(
        agent_name=agent.get("name", "Ассистент"),
        user_name=profile.get("name", "Пользователь"),
        user_role=profile.get("role", "не указана"),
        preferences_text=format_preferences(profile.get("preferences", {})),
        habits_text=format_habits(profile.get("habits", {})),
        context_text=format_context(profile.get("context", {})),
        memory_text=memory_text,
        agent_behavior=agent.get("behavior", "отвечай кратко и по делу"),
        agent_tone=agent.get("tone", "дружелюбный"),
    )


def display_profile(profile):
    """Выводит профиль в терминал."""
    sep = "=" * 55
    print(f"\n{sep}")
    print("  Профиль пользователя")
    print(sep)
    print(f"  Имя:  {profile.get('name', '—')}")
    print(f"  Роль: {profile.get('role', '—')}")
    print()

    prefs = profile.get("preferences", {})
    if prefs:
        print("  Предпочтения:")
        if prefs.get("style"):
            print(f"    Стиль: {prefs['style']}")
        if prefs.get("topics"):
            print(f"    Темы: {', '.join(prefs['topics'])}")

    habits = profile.get("habits", {})
    if habits:
        print("  Привычки:")
        if habits.get("work_hours"):
            print(f"    Часы работы: {habits['work_hours']}")
        if habits.get("tools"):
            print(f"    Инструменты: {', '.join(habits['tools'])}")

    ctx = profile.get("context", {})
    if ctx:
        print("  Контекст:")
        if ctx.get("current_projects"):
            for p in ctx["current_projects"]:
                print(f"    - {p}")

    agent = profile.get("agent", {})
    print(f"\n  Агент: {agent.get('name', '—')} ({agent.get('tone', '—')})")
    print(sep)
    print()
