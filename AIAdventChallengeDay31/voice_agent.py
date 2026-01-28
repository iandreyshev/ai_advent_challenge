#!/usr/bin/env python3
"""
День 31: Голосовой агент (Speech → LLM → Text)

Голосовой агент с распознаванием речи и текстовым выводом через LLM.
Ввод: голосовая команда → текст → LLM → текстовый ответ
"""

import argparse
import sys
import os
import subprocess
import platform
from typing import Optional
from datetime import datetime
import speech_recognition as sr
import requests
import json
from PIL import ImageGrab


class VoiceAgent:
    """Голосовой агент с распознаванием речи и LLM"""

    def __init__(
        self,
        model: str = "qwen2.5",
        host: str = "localhost",
        port: int = 11434,
        recognition_engine: str = "google",
        language: str = "ru-RU"
    ):
        self.model = model
        self.ollama_url = f"http://{host}:{port}/api/generate"
        self.recognition_engine = recognition_engine
        self.language = language
        self.recognizer = sr.Recognizer()

        # Настройки распознавателя для лучшего качества
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

    def listen(self) -> Optional[str]:
        """Захватывает аудио с микрофона и распознаёт речь"""
        with sr.Microphone() as source:
            print("🎤 Говорите... (или скажите 'выход' для завершения)")

            # Калибровка под окружающий шум
            print("⚙️  Калибровка микрофона...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

            try:
                # Захват аудио
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("🔄 Распознавание...")

                # Распознавание речи
                text = self._recognize_speech(audio)
                return text

            except sr.WaitTimeoutError:
                print("⏱️  Время ожидания истекло. Попробуйте ещё раз.")
                return None
            except sr.UnknownValueError:
                print("❌ Не удалось распознать речь. Говорите чётче.")
                return None
            except Exception as e:
                print(f"❌ Ошибка при захвате аудио: {e}")
                return None

    def _recognize_speech(self, audio) -> str:
        """Распознаёт речь с помощью выбранного движка"""
        if self.recognition_engine == "google":
            # Google Speech Recognition (требует интернет)
            return self.recognizer.recognize_google(audio, language=self.language)

        elif self.recognition_engine == "sphinx":
            # CMU Sphinx (работает офлайн, но хуже качество)
            return self.recognizer.recognize_sphinx(audio, language=self.language)

        elif self.recognition_engine == "whisper":
            # OpenAI Whisper API (требует API ключ)
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY не установлен для Whisper")
            return self.recognizer.recognize_whisper_api(audio, api_key=api_key)

        else:
            raise ValueError(f"Неизвестный движок распознавания: {self.recognition_engine}")

    def take_screenshot(self) -> str:
        """Создаёт скриншот экрана и сохраняет в файл"""
        try:
            # Создаём директорию для скриншотов, если её нет
            screenshots_dir = "screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)

            # Генерируем имя файла с текущей датой и временем
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)

            # Захватываем экран
            screenshot = ImageGrab.grab()

            # Сохраняем файл
            screenshot.save(filepath, "PNG")

            # Открываем скриншот в системном просмотрщике
            self._open_file(filepath)

            return f"✅ Скриншот сохранён и открыт: {filepath}"

        except Exception as e:
            return f"❌ Ошибка при создании скриншота: {e}"

    def _open_file(self, filepath: str):
        """Открывает файл в системном приложении по умолчанию"""
        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                subprocess.Popen(["open", filepath],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            elif system == "Windows":
                os.startfile(filepath)
            else:  # Linux
                subprocess.Popen(["xdg-open", filepath],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)

        except Exception as e:
            print(f"⚠️  Не удалось открыть файл: {e}")

    def launch_workspace_apps(self) -> str:
        """Открывает рабочие приложения"""
        try:
            system = platform.system()

            # Список приложений для запуска
            apps = []

            if system == "Darwin":  # macOS
                apps = [
                    ("Google Chrome", "Google Chrome"),
                    ("Visual Studio Code", "Visual Studio Code"),
                    ("Fork", "Fork"),
                    ("Android Studio", "Android Studio"),
                    ("Terminal", "Terminal")
                ]
            elif system == "Windows":
                apps = [
                    ("Google Chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                    ("Visual Studio Code", r"C:\Program Files\Microsoft VS Code\Code.exe"),
                    ("Fork", r"C:\Users\%USERNAME%\AppData\Local\Fork\Fork.exe"),
                    ("Android Studio", r"C:\Program Files\Android\Android Studio\bin\studio64.exe"),
                    ("Windows Terminal", "wt.exe")
                ]
            elif system == "Linux":
                apps = [
                    ("Google Chrome", "google-chrome"),
                    ("Visual Studio Code", "code"),
                    ("Fork", "fork"),
                    ("Android Studio", "android-studio"),
                    ("Terminal", "gnome-terminal")
                ]

            print("🚀 Запуск приложений...")
            launched = []
            failed = []

            for app_name, app_command in apps:
                try:
                    if system == "Darwin":
                        subprocess.Popen(["open", "-a", app_command],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                    elif system == "Windows":
                        subprocess.Popen(app_command,
                                       shell=True,
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                    else:  # Linux
                        subprocess.Popen([app_command],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)

                    launched.append(app_name)
                    print(f"  ✅ {app_name}")

                except Exception as e:
                    failed.append(app_name)
                    print(f"  ❌ {app_name}: {e}")

            # Формируем итоговое сообщение
            result = []
            if launched:
                result.append(f"✅ Запущено приложений: {len(launched)}")
                result.append(f"   {', '.join(launched)}")
            if failed:
                result.append(f"⚠️  Не удалось запустить: {', '.join(failed)}")

            return "\n".join(result) if result else "❌ Не удалось запустить ни одно приложение"

        except Exception as e:
            return f"❌ Ошибка при запуске приложений: {e}"

    def query_llm(self, text: str) -> str:
        """Отправляет текст в LLM и возвращает ответ"""
        try:
            # Определяем язык системного промпта на основе языка распознавания
            if self.language.startswith("ru"):
                system_prompt = "Ты полезный голосовой ассистент. Отвечай кратко и по-русски. Не используй китайский язык."
            else:
                system_prompt = "You are a helpful voice assistant. Answer briefly in English. Do not use Chinese."

            payload = {
                "model": self.model,
                "prompt": text,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 2048
                }
            }

            response = requests.post(self.ollama_url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            return "❌ Не удалось подключиться к Ollama. Убедитесь, что сервер запущен."
        except requests.exceptions.Timeout:
            return "❌ Время ожидания ответа истекло."
        except Exception as e:
            return f"❌ Ошибка при обращении к LLM: {e}"

    def run(self):
        """Основной цикл работы агента"""
        print("=" * 60)
        print("🎙️  ГОЛОСОВОЙ АГЕНТ (Speech → LLM → Text)")
        print("=" * 60)
        print(f"Модель: {self.model}")
        print(f"Движок распознавания: {self.recognition_engine}")
        print(f"Язык: {self.language}")
        print("-" * 60)
        print("Команды:")
        print("  • 'скриншот' или 'screenshot' - сделать снимок экрана")
        print("  • 'просыпайся' или 'папочка вернулся' - запустить рабочие приложения")
        print("  • 'выход' или 'стоп' - завершить работу")
        print("=" * 60)
        print()

        while True:
            # Захват и распознавание голосовой команды
            recognized_text = self.listen()

            if not recognized_text:
                continue

            print(f"📝 Распознано: {recognized_text}")

            # Проверка команды скриншота
            if any(keyword in recognized_text.lower() for keyword in ["скриншот", "screenshot", "снимок экрана", "сделай скриншот"]):
                print("📸 Создание скриншота...")
                result = self.take_screenshot()
                print(result)
                print()
                continue

            # Проверка команды запуска приложений
            if any(keyword in recognized_text.lower() for keyword in ["просыпайся", "папочка вернулся", "wake up", "daddy's home", "запусти приложения"]):
                result = self.launch_workspace_apps()
                print(result)
                print()
                continue

            # Проверка команды выхода
            if recognized_text.lower() in ["выход", "стоп", "exit", "stop", "quit"]:
                print("\n👋 До свидания!")
                break

            # Отправка в LLM
            print("🤖 Обработка запроса...")
            response = self.query_llm(recognized_text)

            # Вывод ответа
            print("\n" + "=" * 60)
            print("💬 ОТВЕТ:")
            print("-" * 60)
            print(response)
            print("=" * 60)
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Голосовой агент с распознаванием речи и LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python3 voice_agent.py
  python3 voice_agent.py --model llama3.2
  python3 voice_agent.py --engine sphinx --language ru-RU
  python3 voice_agent.py --host 192.168.1.100 --port 11434

Движки распознавания:
  google  - Google Speech Recognition (онлайн, хорошее качество)
  sphinx  - CMU Sphinx (офлайн, среднее качество)
  whisper - OpenAI Whisper API (онлайн, требует OPENAI_API_KEY)
        """
    )

    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "qwen2.5"),
        help="Модель Ollama (по умолчанию: qwen2.5)"
    )

    parser.add_argument(
        "--host",
        default=os.getenv("OLLAMA_HOST", "localhost"),
        help="Хост Ollama (по умолчанию: localhost)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("OLLAMA_PORT", "11434")),
        help="Порт Ollama (по умолчанию: 11434)"
    )

    parser.add_argument(
        "--engine",
        choices=["google", "sphinx", "whisper"],
        default="google",
        help="Движок распознавания речи (по умолчанию: google)"
    )

    parser.add_argument(
        "--language",
        default="ru-RU",
        help="Язык распознавания (по умолчанию: ru-RU)"
    )

    args = parser.parse_args()

    # Создание и запуск агента
    agent = VoiceAgent(
        model=args.model,
        host=args.host,
        port=args.port,
        recognition_engine=args.engine,
        language=args.language
    )

    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n\n👋 Прервано пользователем. До свидания!")
        sys.exit(0)


if __name__ == "__main__":
    main()
