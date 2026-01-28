#!/usr/bin/env python3
"""
Демонстрационный скрипт голосового агента
Один запрос → один ответ (для видео-демонстраций)
"""

import argparse
import sys
import speech_recognition as sr
import requests


def listen_once() -> str:
    """Захватывает и распознаёт одну голосовую команду"""
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎤 Калибровка микрофона...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        print("🎙️  Говорите сейчас...")
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)

        print("🔄 Распознавание речи...")
        text = recognizer.recognize_google(audio, language="ru-RU")

        return text


def query_llm(text: str, model: str = "qwen2.5") -> str:
    """Отправляет запрос в LLM"""
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": model,
        "prompt": text,
        "stream": False
    }

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()

    return response.json().get("response", "").strip()


def main():
    parser = argparse.ArgumentParser(description="Демо голосового агента")
    parser.add_argument("--model", default="qwen2.5", help="Модель Ollama")
    args = parser.parse_args()

    print("=" * 70)
    print("🎙️  ГОЛОСОВОЙ АГЕНТ - ДЕМОНСТРАЦИЯ")
    print("=" * 70)
    print()

    try:
        # Шаг 1: Слушаем и распознаём
        recognized_text = listen_once()

        print("\n" + "=" * 70)
        print("📝 РАСПОЗНАННЫЙ ТЕКСТ:")
        print("-" * 70)
        print(recognized_text)
        print("=" * 70)
        print()

        # Шаг 2: Отправляем в LLM
        print("🤖 Отправка запроса в LLM...")
        response = query_llm(recognized_text, args.model)

        # Шаг 3: Выводим ответ
        print("\n" + "=" * 70)
        print("💬 ОТВЕТ LLM:")
        print("-" * 70)
        print(response)
        print("=" * 70)
        print()

        print("✅ Демонстрация завершена")

    except sr.WaitTimeoutError:
        print("❌ Время ожидания речи истекло")
        sys.exit(1)
    except sr.UnknownValueError:
        print("❌ Не удалось распознать речь")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
