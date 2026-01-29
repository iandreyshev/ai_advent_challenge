"""Создание скриншотов экрана."""

import os
import platform
import subprocess
from datetime import datetime


def take_screenshot(output_dir: str = "screenshots") -> str:
    """
    Создаёт скриншот экрана и сохраняет в файл.
    Возвращает сообщение с результатом.
    """
    try:
        # Создаём директорию для скриншотов
        os.makedirs(output_dir, exist_ok=True)

        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        system = platform.system()

        if system == "Darwin":  # macOS — используем нативный screencapture
            # -x отключает звук, делает скриншот всего экрана мгновенно
            result = subprocess.run(
                ["screencapture", "-x", filepath],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                return f"❌ Ошибка screencapture: {result.stderr.decode()}"
        else:
            # Windows/Linux — используем PIL
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(filepath, "PNG")

        # Открываем скриншот
        _open_file(filepath)

        return f"✅ Скриншот сохранён: {filepath}"

    except Exception as e:
        return f"❌ Ошибка при создании скриншота: {e}"


def _open_file(filepath: str) -> None:
    """Открывает файл в системном приложении."""
    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            subprocess.Popen(
                ["open", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif system == "Windows":
            os.startfile(filepath)
        else:  # Linux
            subprocess.Popen(
                ["xdg-open", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    except Exception as e:
        print(f"⚠️  Не удалось открыть файл: {e}")
