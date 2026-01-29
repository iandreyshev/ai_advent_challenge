"""Распознавание речи с микрофона."""

import speech_recognition as sr
from typing import Optional


class VoiceRecognition:
    """Распознавание речи с различными движками."""

    def __init__(self, engine: str = "google", language: str = "ru-RU"):
        """
        Инициализация распознавателя речи.

        Args:
            engine: Движок распознавания (google, sphinx, whisper)
            language: Язык распознавания (ru-RU, en-US, etc.)
        """
        self.engine = engine
        self.language = language
        self.recognizer = sr.Recognizer()

        # Настройки для лучшего качества
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

    def listen(self) -> Optional[str]:
        """
        Захватывает аудио с микрофона и распознаёт речь.
        Возвращает распознанный текст или None.
        """
        with sr.Microphone() as source:
            print("🎤 Говорите... (или скажите 'выход')")

            # Калибровка под окружающий шум
            print("⚙️  Калибровка микрофона...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

            try:
                # Захват аудио
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("🔄 Распознавание...")

                # Распознавание речи
                text = self._recognize(audio)
                return text

            except sr.WaitTimeoutError:
                print("⏱️  Время ожидания истекло.")
                return None
            except sr.UnknownValueError:
                print("❌ Не удалось распознать речь. Говорите чётче.")
                return None
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                return None

    def _recognize(self, audio) -> str:
        """Распознаёт речь с помощью выбранного движка."""
        if self.engine == "google":
            # Google Speech Recognition (онлайн)
            return self.recognizer.recognize_google(audio, language=self.language)

        elif self.engine == "sphinx":
            # CMU Sphinx (офлайн)
            return self.recognizer.recognize_sphinx(audio, language=self.language)

        elif self.engine == "whisper":
            # OpenAI Whisper API
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY не установлен для Whisper")
            return self.recognizer.recognize_whisper_api(audio, api_key=api_key)

        else:
            raise ValueError(f"Неизвестный движок: {self.engine}")
