#!/usr/bin/env python3
"""
Тестовый скрипт для проверки микрофона и распознавания речи
Проверяет работоспособность без LLM
"""

import speech_recognition as sr


def test_microphone_list():
    """Выводит список доступных микрофонов"""
    print("=" * 60)
    print("🎤 ДОСТУПНЫЕ МИКРОФОНЫ")
    print("=" * 60)

    try:
        mic_list = sr.Microphone.list_microphone_names()
        for i, name in enumerate(mic_list):
            print(f"{i}: {name}")
        print("=" * 60)
        return len(mic_list) > 0
    except Exception as e:
        print(f"❌ Ошибка при получении списка микрофонов: {e}")
        return False


def test_speech_recognition():
    """Тестирует распознавание речи"""
    print("\n" + "=" * 60)
    print("🎙️  ТЕСТ РАСПОЗНАВАНИЯ РЕЧИ")
    print("=" * 60)

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("⚙️  Калибровка под окружающий шум...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            print("🎤 Говорите что-нибудь...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            print("🔄 Распознавание...")

            # Пробуем разные движки
            engines_results = {}

            # Google Speech Recognition
            try:
                text = recognizer.recognize_google(audio, language="ru-RU")
                engines_results["Google"] = text
            except sr.UnknownValueError:
                engines_results["Google"] = "❌ Не удалось распознать"
            except Exception as e:
                engines_results["Google"] = f"❌ Ошибка: {e}"

            # Выводим результаты
            print("\n" + "=" * 60)
            print("📝 РЕЗУЛЬТАТЫ")
            print("=" * 60)

            for engine, result in engines_results.items():
                print(f"\n{engine}:")
                print(f"  {result}")

            print("\n" + "=" * 60)
            return True

    except sr.WaitTimeoutError:
        print("⏱️  Время ожидания истекло")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def main():
    print("🧪 ПРОВЕРКА СИСТЕМЫ РАСПОЗНАВАНИЯ РЕЧИ\n")

    # Тест 1: Список микрофонов
    has_microphones = test_microphone_list()

    if not has_microphones:
        print("\n❌ Микрофоны не найдены. Проверьте подключение.")
        return

    # Тест 2: Распознавание речи
    test_speech_recognition()

    print("\n✅ Тестирование завершено")


if __name__ == "__main__":
    main()
