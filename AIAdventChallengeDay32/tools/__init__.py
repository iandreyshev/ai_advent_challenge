"""
God Agent Tools - модульная система инструментов для универсального AI-агента.

Включает:
- Голосовое управление (распознавание речи)
- Персональная память и профиль
- Анализ данных (CSV/JSON)
- Скриншоты экрана
- Запуск приложений
- LLM интеграция (Ollama)
"""

from .llm import OllamaClient
from .memory import Memory
from .profile import Profile
from .analytics import DataAnalytics
from .screenshot import take_screenshot
from .launcher import launch_workspace_apps, launch_app, list_installed_apps, get_launcher, AppLauncher

# VoiceRecognition — опциональный (требует SpeechRecognition + PyAudio)
try:
    from .voice import VoiceRecognition
    VOICE_AVAILABLE = True
except ImportError:
    VoiceRecognition = None
    VOICE_AVAILABLE = False

__all__ = [
    "OllamaClient",
    "Memory",
    "Profile",
    "DataAnalytics",
    "VoiceRecognition",
    "take_screenshot",
    "launch_workspace_apps",
    "launch_app",
    "list_installed_apps",
    "get_launcher",
    "AppLauncher",
    "VOICE_AVAILABLE",
]
