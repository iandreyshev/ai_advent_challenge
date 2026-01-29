"""Анализ данных из CSV и JSON файлов."""

import csv
import json
import os
from collections import Counter
from typing import Dict, List, Tuple, Any


class DataAnalytics:
    """Загрузка и анализ данных из файлов."""

    def __init__(self):
        self.data: List[Dict[str, Any]] = []
        self.data_type: str = ""
        self.summary: Dict[str, Any] = {}
        self.filepath: str = ""

    def load_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Загружает данные из файла.
        Возвращает (success, message).
        """
        if not os.path.exists(filepath):
            return False, f"Файл не найден: {filepath}"

        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext == ".csv":
                return self._load_csv(filepath)
            elif ext == ".json":
                return self._load_json(filepath)
            else:
                return False, f"Неподдерживаемый формат: {ext}. Используйте .csv или .json"
        except Exception as e:
            return False, f"Ошибка загрузки: {e}"

    def _load_csv(self, filepath: str) -> Tuple[bool, str]:
        """Загружает CSV файл."""
        with open(filepath, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        if not rows:
            return False, "CSV файл пуст"

        columns = list(rows[0].keys())
        value_counts = {}

        for col in columns:
            values = [r[col] for r in rows if r.get(col)]
            value_counts[col] = Counter(values).most_common(10)

        self.data = rows
        self.data_type = "CSV"
        self.filepath = filepath
        self.summary = {
            "row_count": len(rows),
            "columns": columns,
            "value_counts": value_counts,
        }

        return True, f"✅ Загружено {len(rows)} строк, {len(columns)} колонок"

    def _load_json(self, filepath: str) -> Tuple[bool, str]:
        """Загружает JSON файл."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        if not data:
            return False, "JSON файл пуст"

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

        self.data = data
        self.data_type = "JSON"
        self.filepath = filepath
        self.summary = {
            "record_count": len(data),
            "fields": sorted(all_keys),
            "value_counts": value_counts,
        }

        return True, f"✅ Загружено {len(data)} записей, {len(all_keys)} полей"

    def get_summary_text(self) -> str:
        """Возвращает текстовую сводку по данным."""
        if not self.data:
            return "Нет загруженных данных."

        lines = [f"📊 СВОДКА ПО ДАННЫМ: {os.path.basename(self.filepath)}"]
        lines.append("=" * 60)

        if self.data_type == "CSV":
            lines.append(f"Формат: CSV")
            lines.append(f"Строк: {self.summary['row_count']}")
            lines.append(f"Колонки: {', '.join(self.summary['columns'])}")
        else:
            lines.append(f"Формат: JSON")
            lines.append(f"Записей: {self.summary['record_count']}")
            lines.append(f"Поля: {', '.join(self.summary['fields'])}")

        lines.append("\nЧастотный анализ (топ значений):")
        for col, counts in list(self.summary["value_counts"].items())[:5]:
            if counts:
                lines.append(f"\n  [{col}]")
                for value, count in counts[:5]:
                    lines.append(f"    {value}: {count}")

        return "\n".join(lines)

    def get_context_for_llm(self, max_records: int = 100) -> str:
        """Возвращает контекст для LLM."""
        if not self.data:
            return "Нет загруженных данных."

        lines = [
            f"Файл: {os.path.basename(self.filepath)}",
            f"Формат: {self.data_type}",
            "",
            self.get_summary_text(),
            "",
            "Первые записи:",
        ]

        for i, record in enumerate(self.data[:max_records], 1):
            lines.append(f"{i}. {json.dumps(record, ensure_ascii=False)}")

        if len(self.data) > max_records:
            lines.append(f"\n... и ещё {len(self.data) - max_records} записей")

        return "\n".join(lines)

    def is_loaded(self) -> bool:
        """Проверяет, загружены ли данные."""
        return len(self.data) > 0
