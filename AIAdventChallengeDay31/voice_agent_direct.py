#!/usr/bin/env python3
"""
День 31: Голосовой агент с прямой отправкой аудио в модель

Архитектура:
1. Запись аудио в файл (WAV)
2. Отправка аудио в модель распознавания (Whisper)
3. Получение текста
4. Отправка в LLM
5. Вывод ответа
"""

import argparse
import sys
import os
import wave
import tempfile
from typing import Optional
import pyaudio
import requests


class DirectVoiceAgent:
    """Голосовой агент с прямой отправкой аудио в модель"""

    def __init__(
        self,
        llm_model: str = "qwen2.5",
        whisper_mode: str = "api",  # "api" или "local"
        host: str = "localhost",
        port: int = 11434,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        record_seconds: int = 5
    ):
        self.llm_model = llm_model
        self.whisper_mode = whisper_mode
        self.ollama_url = f"http://{host}:{port}/api/generate"
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.record_seconds = record_seconds

        # Whisper API настройки
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if whisper_mode == "api" and not self.openai_api_key:
            print("⚠️  OPENAI_API_KEY не установлен. Используйте --mode local")

        # PyAudio
        self.audio = pyaudio.PyAudio()

    def record_audio(self) -> Optional[str]:
        """Записывает аудио с микрофона и сохраняет во временный файл"""
        print("🎤 Говорите сейчас...")

        try:
            # Открываем поток для записи
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            frames = []

            # Записываем аудио
            for i in range(0, int(self.sample_rate / self.chunk_size * self.record_seconds)):
                data = stream.read(self.chunk_size)
                frames.append(data)

                # Индикатор записи
                if i % 10 == 0:
                    print(".", end="", flush=True)

            print("\n✅ Запись завершена")

            # Закрываем поток
            stream.stop_stream()
            stream.close()

            # Сохраняем во временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_filename = temp_file.name

            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))

            return temp_filename

        except Exception as e:
            print(f"❌ Ошибка при записи: {e}")
            return None

    def transcribe_audio_api(self, audio_file: str) -> Optional[str]:
        """Отправляет аудио в OpenAI Whisper API для распознавания"""
        print("🔄 Отправка в Whisper API...")

        try:
            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}"
            }

            with open(audio_file, "rb") as f:
                files = {
                    "file": (os.path.basename(audio_file), f, "audio/wav"),
                    "model": (None, "whisper-1"),
                    "language": (None, "ru")
                }

                response = requests.post(url, headers=headers, files=files, timeout=30)
                response.raise_for_status()

                result = response.json()
                return result.get("text", "").strip()

        except requests.exceptions.ConnectionError:
            print("❌ Ошибка подключения к OpenAI API")
            return None
        except requests.exceptions.Timeout:
            print("❌ Таймаут при обращении к Whisper API")
            return None
        except Exception as e:
            print(f"❌ Ошибка при распознавании: {e}")
            return None

    def transcribe_audio_local(self, audio_file: str) -> Optional[str]:
        """Использует локальную модель для распознавания (через Ollama с Whisper)"""
        print("🔄 Распознавание через локальную модель...")

        # Примечание: Ollama пока не поддерживает аудио напрямую
        # Это заглушка для будущей реализации
        # Можно использовать локальный Whisper через whisper-cpp или faster-whisper

        try:
            import whisper

            print("📥 Загрузка модели Whisper...")
            model = whisper.load_model("base")

            print("🎯 Распознавание...")
            result = model.transcribe(audio_file, language="ru")

            return result.get("text", "").strip()

        except ImportError:
            print("❌ Библиотека openai-whisper не установлена")
            print("   Установите: pip install openai-whisper")
            return None
        except Exception as e:
            print(f"❌ Ошибка при распознавании: {e}")
            return None

    def transcribe_audio(self, audio_file: str) -> Optional[str]:
        """Распознаёт аудио выбранным способом"""
        if self.whisper_mode == "api":
            return self.transcribe_audio_api(audio_file)
        else:
            return self.transcribe_audio_local(audio_file)

    def query_llm(self, text: str) -> str:
        """Отправляет текст в LLM и возвращает ответ"""
        try:
            payload = {
                "model": self.llm_model,
                "prompt": text,
                "stream": False
            }

            response = requests.post(self.ollama_url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            return "❌ Не удалось подключиться к Ollama"
        except requests.exceptions.Timeout:
            return "❌ Время ожидания ответа истекло"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def run(self):
        """Основной цикл работы агента"""
        print("=" * 60)
        print("🎙️  ГОЛОСОВОЙ АГЕНТ (Direct Audio → Whisper → LLM)")
        print("=" * 60)
        print(f"LLM модель: {self.llm_model}")
        print(f"Whisper режим: {self.whisper_mode}")
        print(f"Длительность записи: {self.record_seconds} сек")
        print("-" * 60)
        print("Команды: скажите 'выход' для завершения")
        print("=" * 60)
        print()

        while True:
            # Шаг 1: Запись аудио
            audio_file = self.record_audio()
            if not audio_file:
                continue

            try:
                # Шаг 2: Распознавание речи
                recognized_text = self.transcribe_audio(audio_file)

                if not recognized_text:
                    print("⚠️  Не удалось распознать речь. Попробуйте ещё раз.")
                    continue

                print(f"📝 Распознано: {recognized_text}")

                # Проверка команды выхода
                if recognized_text.lower() in ["выход", "стоп", "exit", "stop", "quit"]:
                    print("\n👋 До свидания!")
                    break

                # Шаг 3: Отправка в LLM
                print("🤖 Обработка запроса...")
                response = self.query_llm(recognized_text)

                # Шаг 4: Вывод ответа
                print("\n" + "=" * 60)
                print("💬 ОТВЕТ:")
                print("-" * 60)
                print(response)
                print("=" * 60)
                print()

            finally:
                # Удаляем временный файл
                if os.path.exists(audio_file):
                    os.remove(audio_file)

    def __del__(self):
        """Очистка ресурсов"""
        if hasattr(self, 'audio'):
            self.audio.terminate()


def main():
    parser = argparse.ArgumentParser(
        description="Голосовой агент с прямой отправкой аудио в модель",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # С OpenAI Whisper API (требует OPENAI_API_KEY)
  python3 voice_agent_direct.py --mode api

  # С локальным Whisper (требует pip install openai-whisper)
  python3 voice_agent_direct.py --mode local

  # Изменить длительность записи
  python3 voice_agent_direct.py --duration 10

  # Другая LLM модель
  python3 voice_agent_direct.py --model llama3.2

Преимущества прямой отправки аудио:
- Больше контроля над процессом записи
- Возможность использовать продвинутые модели
- Сохранение аудио для отладки (опционально)
- Работа с локальными моделями без интернета
        """
    )

    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "qwen2.5"),
        help="LLM модель (по умолчанию: qwen2.5)"
    )

    parser.add_argument(
        "--mode",
        choices=["api", "local"],
        default="api",
        help="Режим Whisper: api (OpenAI) или local (локальная модель)"
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
        "--duration",
        type=int,
        default=5,
        help="Длительность записи в секундах (по умолчанию: 5)"
    )

    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Частота дискретизации (по умолчанию: 16000)"
    )

    args = parser.parse_args()

    # Создание и запуск агента
    agent = DirectVoiceAgent(
        llm_model=args.model,
        whisper_mode=args.mode,
        host=args.host,
        port=args.port,
        sample_rate=args.sample_rate,
        record_seconds=args.duration
    )

    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n\n👋 Прервано пользователем. До свидания!")
        sys.exit(0)


if __name__ == "__main__":
    main()
