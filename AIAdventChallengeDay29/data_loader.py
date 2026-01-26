"""Утилиты для загрузки и анализа данных из CSV и JSON файлов."""

import csv
import json
import os
from collections import Counter


def load_csv(filepath):
    """Загружает CSV и возвращает (rows, summary)."""
    with open(filepath, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return [], {"row_count": 0, "columns": [], "value_counts": {}}

    columns = list(rows[0].keys())

    value_counts = {}
    for col in columns:
        values = [r[col] for r in rows if r.get(col)]
        value_counts[col] = Counter(values).most_common(10)

    return rows, {
        "row_count": len(rows),
        "columns": columns,
        "value_counts": value_counts,
    }


def load_json(filepath):
    """Загружает JSON (массив объектов) и возвращает (records, summary)."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    if not data:
        return [], {"record_count": 0, "fields": [], "value_counts": {}}

    all_keys = set()
    for item in data:
        if isinstance(item, dict):
            all_keys.update(item.keys())

    value_counts = {}
    for key in sorted(all_keys):
        values = [item.get(key) for item in data if isinstance(item, dict) and key in item]
        try:
            value_counts[key] = Counter(values).most_common(10)
        except TypeError:
            value_counts[key] = [("(сложные объекты)", len(values))]

    return data, {
        "record_count": len(data),
        "fields": sorted(all_keys),
        "value_counts": value_counts,
    }


def format_statistics(data_type, summary):
    """Форматирует статистику в текст."""
    lines = []

    if data_type == "csv":
        lines.append(f"Строк: {summary['row_count']}")
        lines.append(f"Колонки: {', '.join(summary['columns'])}")
    else:
        lines.append(f"Записей: {summary['record_count']}")
        lines.append(f"Поля: {', '.join(summary['fields'])}")

    lines.append("\nЧастотный анализ:")
    for col, counts in summary["value_counts"].items():
        if counts:
            lines.append(f"\n  [{col}]")
            for value, count in counts[:7]:
                lines.append(f"    {value}: {count}")

    return "\n".join(lines)


def format_full_data(data, max_records=150):
    """Форматирует данные для LLM контекста."""
    lines = []
    for i, record in enumerate(data[:max_records], 1):
        lines.append(f"{i}. {json.dumps(record, ensure_ascii=False)}")
    if len(data) > max_records:
        lines.append(f"\n... и ещё {len(data) - max_records} записей (не показаны)")
    return "\n".join(lines)


def load_file(filepath):
    """
    Загружает файл данных.

    Возвращает (data_type, data, summary).
    Поддерживает: .csv, .json
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".csv":
        data, summary = load_csv(filepath)
        return "CSV", data, summary
    elif ext == ".json":
        data, summary = load_json(filepath)
        return "JSON", data, summary
    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}. Используйте .csv или .json")
