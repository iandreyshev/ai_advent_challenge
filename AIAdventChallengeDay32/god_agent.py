#!/usr/bin/env python3
"""
День 32: God Agent — универсальный персональный AI-ассистент.

Объединяет функции всех предыдущих проектов:
- Голосовое управление (Day 31)
- Персональная память и профиль (Day 30)
- Анализ данных (Day 29)
- Скриншоты и запуск приложений

Запуск:
    python3 god_agent.py                    # текстовый режим
    python3 god_agent.py --voice            # голосовой режим
    python3 god_agent.py --profile custom.yaml
    python3 god_agent.py --model llama3
"""

import argparse
import sys
import os
from typing import List, Dict

from tools import (
    OllamaClient,
    Memory,
    Profile,
    DataAnalytics,
    VoiceRecognition,
    take_screenshot,
    launch_workspace_apps,
    launch_app,
    list_installed_apps,
    get_launcher,
    VOICE_AVAILABLE,
)


class GodAgent:
    """Универсальный персональный AI-ассистент."""

    def __init__(
        self,
        model: str = "llama3.1",
        profile_file: str = "profile.yaml",
        voice_mode: bool = False,
        voice_engine: str = "google",
        voice_language: str = "ru-RU",
    ):
        # Инициализация компонентов
        self.llm = OllamaClient(model=model)
        self.memory = Memory()
        self.profile = Profile(profile_file)
        self.analytics = DataAnalytics()
        self.voice_mode = voice_mode and VOICE_AVAILABLE

        if voice_mode and not VOICE_AVAILABLE:
            print("⚠️  Голосовой режим недоступен: требуется SpeechRecognition и PyAudio")
            print("   Установите: pip3 install SpeechRecognition PyAudio")
            print("   Запускаю в текстовом режиме...\n")

        if self.voice_mode:
            self.voice = VoiceRecognition(engine=voice_engine, language=voice_language)
        else:
            self.voice = None

        # Инициализируем launcher с LLM matcher
        get_launcher(self._llm_app_matcher)

        # История сообщений
        self.messages: List[Dict[str, str]] = []
        self._rebuild_system_prompt()

    def _rebuild_system_prompt(self) -> None:
        """Пересобирает системный промпт с профилем и памятью."""
        memory_text = self.memory.format_for_prompt()
        system_prompt = self.profile.build_system_prompt(memory_text)

        # Добавляем информацию о загруженных данных
        if self.analytics.is_loaded():
            system_prompt += f"\n\nТекущие загруженные данные:\n{self.analytics.get_summary_text()}"

        # Обновляем системное сообщение
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0] = {"role": "system", "content": system_prompt}
        else:
            self.messages.insert(0, {"role": "system", "content": system_prompt})

    def handle_command(self, cmd: str) -> bool:
        """
        Обработка команд, начинающихся с /.
        Возвращает True если команда обработана, False для выхода.
        """
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if command == "/help":
            self._print_help()
            return True

        elif command == "/profile":
            self.profile.display()
            return True

        elif command == "/memory":
            self.memory.display()
            return True

        elif command == "/remember":
            if not arg:
                print("Использование: /remember <факт>")
                return True
            user_name = self.profile.get("name", "Пользователь")
            fact = self._rephrase_fact(arg, user_name)
            if self.memory.add_fact(fact, source="manual"):
                print(f"✅ Запомнил: {fact}")
                self._rebuild_system_prompt()
            else:
                print("⚠️  Этот факт уже сохранён.")
            return True

        elif command == "/forget":
            self.memory.clear()
            print("✅ Память очищена.")
            self._rebuild_system_prompt()
            return True

        elif command == "/clear":
            system_msg = self.messages[0]
            self.messages = [system_msg]
            print("✅ История чата очищена.")
            return True

        elif command == "/model":
            if not arg:
                print(f"Текущая модель: {self.llm.model}")
                print("Использование: /model <имя>")
                return True
            self.llm.model = arg
            print(f"✅ Модель изменена на: {arg}")
            return True

        elif command == "/load":
            if not arg:
                print("Использование: /load <путь_к_файлу>")
                return True
            success, message = self.analytics.load_file(arg)
            print(message)
            if success:
                self._rebuild_system_prompt()
                print("\n" + self.analytics.get_summary_text())
            return True

        elif command == "/screenshot":
            result = take_screenshot()
            print(result)
            return True

        elif command == "/launch":
            result = launch_workspace_apps()
            print(result)
            return True

        elif command == "/app":
            if not arg:
                print("Использование: /app <название или описание>")
                print("Примеры: /app telegram, /app браузер, /app код")
                return True
            result = launch_app(arg)
            print(result)
            return True

        elif command == "/apps":
            result = list_installed_apps(arg)
            print(result)
            return True

        elif command == "/voice":
            if self.voice_mode:
                print("⚠️  Голосовой режим уже активен.")
            else:
                print("⚠️  Голосовой режим не был включён при запуске.")
                print("   Перезапустите с флагом --voice")
            return True

        elif command in ["/exit", "/quit"]:
            return False

        else:
            print(f"❌ Неизвестная команда: {command}")
            print("   Введите /help для списка команд.")
            return True

    def _llm_app_matcher(self, query: str, candidates: List[str]) -> str:
        """Умный поиск приложения через LLM."""
        # Ограничиваем список кандидатов для промпта
        candidates_list = candidates[:50]
        candidates_str = ", ".join(candidates_list)

        prompt = f"""Найди наиболее подходящее приложение для запроса пользователя.

Запрос: "{query}"

Доступные приложения: {candidates_str}

Ответь ТОЛЬКО названием одного приложения из списка, которое лучше всего соответствует запросу.
Если ничего не подходит, ответь "нет".

Приложение:"""

        try:
            result = self.llm.generate(prompt, temperature=0.1, num_predict=30)
            result = result.strip().strip('"').strip("'")

            # Проверяем, что результат есть в списке кандидатов
            for app in candidates:
                if app.lower() == result.lower():
                    return app

            # Частичное совпадение
            for app in candidates:
                if result.lower() in app.lower() or app.lower() in result.lower():
                    return app

        except Exception:
            pass

        return candidates[0] if candidates else ""

    def _interpret_voice_intent(self, text: str) -> tuple[str, str]:
        """
        Интерпретирует голосовой ввод через LLM и определяет намерение.

        Возвращает (intent, argument):
        - ("command", "/screenshot") — выполнить команду
        - ("command", "/remember Я люблю кофе") — команда с аргументом
        - ("text", "original text") — обычный текст для чата
        """
        # Получаем список установленных приложений для LLM
        launcher = get_launcher()
        apps_list = launcher.get_installed_apps()
        apps_sample = ", ".join(apps_list[:80])  # Первые 80 для промпта

        prompt = f"""Ты классификатор голосовых команд. Определи намерение пользователя.

ПРИОРИТЕТ: Если пользователь просит ОТКРЫТЬ, ЗАПУСТИТЬ, ВКЛЮЧИТЬ что-то — это ВСЕГДА команда /app!

УСТАНОВЛЕННЫЕ ПРИЛОЖЕНИЯ (используй ТОЧНЫЕ названия):
{apps_sample}

ПРАВИЛА КЛАССИФИКАЦИИ:
1. /app <название> — запуск приложения. Ключевые слова: "запусти", "открой", "включи", "покажи", "зайди в"
2. /launch — ТОЛЬКО фразы: "просыпайся", "папочка вернулся", "запусти всё", "рабочее окружение"
3. /screenshot — "скриншот", "снимок экрана", "сфоткай"
4. /help — "справка", "помощь", "что умеешь"
5. /profile — "покажи профиль", "кто я"
6. /memory — "что помнишь", "покажи память"
7. /remember <факт> — "запомни" + информация о пользователе
8. /forget — "забудь всё", "очисти память"
9. /clear — "очисти чат", "новый разговор"
10. /apps — "список приложений", "какие приложения"
11. exit — "выход", "пока", "до свидания"
12. text — вопросы, просьбы посчитать, общение (НЕ связанное с запуском программ)

КОМАНДА ПОЛЬЗОВАТЕЛЯ: "{text}"

ПРИМЕРЫ → ОТВЕТЫ:
"запусти xcode" → /app Xcode
"открой телеграм" → /app Telegram
"включи браузер" → /app Safari
"открой код" → /app Visual Studio Code
"зайди в андроид студио" → /app Android Studio
"сколько будет 2+2" → text
"расскажи анекдот" → text

ВАЖНО: Если есть ЛЮБОЕ упоминание запуска/открытия программы — выбери /app с ТОЧНЫМ названием из списка!

Ответ (только команда или text):"""

        try:
            # DEBUG: раскомментируйте для просмотра полного промпта
            # print(f"📋 ПРОМПТ:\n{prompt}\n{'='*50}")
            result = self.llm.generate(prompt, temperature=0.1, num_predict=50)
            result = result.strip()
            print(f"🔍 LLM вернул: '{result}'")  # DEBUG

            # Проверяем, это команда или текст
            # LLM иногда возвращает "/text" вместо "text"
            if result.lower() in ["text", "/text"] or not result:
                return ("text", text)

            # Если начинается с / — это команда
            if result.startswith("/"):
                return ("command", result)

            # Проверяем на exit
            if result.lower() in ["exit", "quit", "выход"]:
                return ("command", "exit")

            # Если LLM вернула что-то другое — считаем текстом
            return ("text", text)

        except Exception as e:
            print(f"⚠️  Ошибка интерпретации: {e}")
            return ("text", text)

    def _rephrase_fact(self, fact: str, user_name: str) -> str:
        """Перефразирует факт от третьего лица через LLM."""
        prompt = f"""Перефрази следующий факт от третьего лица об пользователе {user_name}.
Ответь только перефразированным фактом, без объяснений.

Факт: {fact}

Перефразированный факт (от третьего лица):"""

        try:
            result = self.llm.generate(prompt, temperature=0.3, num_predict=80)
            if result and len(result) > 3 and len(result) < 300:
                return result
        except Exception:
            pass

        return fact

    def _try_extract_fact(self, user_message: str) -> str:
        """Пытается извлечь важный факт из сообщения пользователя."""
        user_name = self.profile.get("name", "Пользователь")
        prompt = f"""Проанализируй сообщение пользователя {user_name}.
Если оно содержит важный факт для запоминания (предпочтение, привычка, информация о себе),
сформулируй его от третьего лица в одно предложение.
Если факта нет, ответь "нет".

Сообщение: {user_message}

Факт (или "нет"):"""

        try:
            fact = self.llm.generate(prompt, temperature=0.2, num_predict=80)
            if fact and fact.lower() != "нет" and len(fact) > 5 and len(fact) < 300:
                return fact
        except Exception:
            pass

        return ""

    def _print_help(self) -> None:
        """Выводит справку по командам."""
        sep = "=" * 60
        print(f"\n{sep}")
        print("⚡️ GOD AGENT — КОМАНДЫ")
        print(sep)
        print("Профиль и память:")
        print("  /profile              — показать профиль")
        print("  /remember <факт>      — запомнить факт")
        print("  /memory               — показать память")
        print("  /forget               — очистить память")
        print()
        print("Управление:")
        print("  /clear                — очистить историю чата")
        print("  /model <имя>          — сменить модель")
        print("  /help                 — эта справка")
        print()
        print("Инструменты:")
        print("  /load <файл>          — загрузить данные (CSV/JSON)")
        print("  /screenshot           — сделать скриншот экрана")
        print("  /app <название>       — запустить приложение (умный поиск)")
        print("  /apps [фильтр]        — список установленных приложений")
        print("  /launch               — запустить рабочее окружение")
        print()
        print("Голосовые команды (в голосовом режиме):")
        print("  ИИ понимает намерение — говорите своими словами!")
        print("  Примеры:")
        print("    'открой телеграм' / 'запусти хром' → /app ...")
        print("    'сделай скриншот' / 'сфоткай'      → /screenshot")
        print("    'просыпайся' / 'рабочие программы' → /launch")
        print("    'покажи профиль' / 'кто я?'        → /profile")
        print("    'что ты помнишь?' / 'память'       → /memory")
        print("    'запомни что я люблю кофе'         → /remember ...")
        print("    'загрузи файл data.csv'            → /load ...")
        print("    'очисти историю'                   → /clear")
        print()
        print("Выход:")
        print("  /exit, /quit, exit, quit")
        print(sep)

    def _print_welcome(self) -> None:
        """Выводит приветственное сообщение."""
        sep = "=" * 60
        agent_name = self.profile.get("agent", {}).get("name", "God Agent")
        user_name = self.profile.get("name", "Пользователь")

        print(sep)
        print(f"⚡️ {agent_name.upper()}")
        print(sep)
        print(f"Модель: {self.llm.model}")
        print(f"Пользователь: {user_name}")
        print(f"Режим: {'🎤 Голосовой' if self.voice_mode else '⌨️  Текстовый'}")

        if len(self.memory) > 0:
            print(f"Загружено фактов: {len(self.memory)}")

        print(sep)
        print("Введите /help для списка команд")
        print(sep)
        print()

        # Приветствие агента
        greeting = self.profile.get("agent", {}).get("greeting", "Привет! Чем могу помочь?")
        greeting = greeting.replace("{user_name}", user_name)
        print(f"{agent_name}: {greeting}\n")

    def run(self) -> None:
        """Основной цикл работы агента."""
        self._print_welcome()

        while True:
            try:
                # Получение ввода (голос или текст)
                if self.voice_mode:
                    user_input = self.voice.listen()
                    if not user_input:
                        continue
                    print(f"📝 Распознано: {user_input}")
                else:
                    user_input = input("Вы: ").strip()

                if not user_input:
                    continue

                # Проверка команды выхода (текстовый режим)
                if user_input.lower() in ["выход", "exit", "quit", "q"]:
                    print("\n👋 До свидания!")
                    break

                # Обработка команд, начинающихся с /
                if user_input.startswith("/"):
                    should_continue = self.handle_command(user_input)
                    if not should_continue:
                        print("\n👋 До свидания!")
                        break
                    continue

                # Интеллектуальная интерпретация голосовых команд
                if self.voice_mode:
                    print("🤔 Анализирую намерение...")
                    intent, value = self._interpret_voice_intent(user_input)

                    if intent == "command":
                        print(f"🎯 Распознана команда: {value}")

                        # Команда выхода
                        if value.lower() in ["exit", "quit", "выход"]:
                            print("\n👋 До свидания!")
                            break

                        # Команда /screenshot
                        if value == "/screenshot":
                            result = take_screenshot()
                            print(result)
                            continue

                        # Команда /launch
                        if value == "/launch":
                            result = launch_workspace_apps()
                            print(result)
                            continue

                        # Команда /app <название>
                        if value.startswith("/app "):
                            app_query = value[5:].strip()
                            if app_query:
                                result = launch_app(app_query)
                                print(result)
                            continue

                        # Остальные команды обрабатываем через handle_command
                        if value.startswith("/"):
                            should_continue = self.handle_command(value)
                            if not should_continue:
                                print("\n👋 До свидания!")
                                break
                            continue

                    # Если intent == "text", продолжаем как обычное сообщение
                    print("💬 Обрабатываю как сообщение...")

                # Обычное сообщение в LLM
                self.messages.append({"role": "user", "content": user_input})

                agent_name = self.profile.get("agent", {}).get("name", "God Agent")
                print(f"\n{agent_name}: ", end="", flush=True)

                try:
                    response = self.llm.chat_streaming(self.messages)
                    self.messages.append({"role": "assistant", "content": response})

                    # Автоматическое извлечение фактов
                    fact = self._try_extract_fact(user_input)
                    if fact:
                        if self.memory.add_fact(fact, source="auto"):
                            print(f"\n💾 [запомнил: {fact}]")
                            self._rebuild_system_prompt()

                except ConnectionError as e:
                    print(f"\n❌ {e}")
                    print("   Убедитесь, что Ollama запущена: ollama serve")
                    self.messages.pop()
                except Exception as e:
                    print(f"\n❌ Ошибка: {e}")
                    self.messages.pop()

                print()  # Пустая строка для разделения

            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 До свидания!")
                break


def main():
    parser = argparse.ArgumentParser(
        description="God Agent — универсальный персональный AI-ассистент",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python3 god_agent.py                           # текстовый режим
  python3 god_agent.py --voice                   # голосовой режим
  python3 god_agent.py --profile custom.yaml     # кастомный профиль
  python3 god_agent.py --model llama3            # другая модель
  python3 god_agent.py --voice --engine sphinx   # офлайн распознавание

Возможности:
  ✅ Персональная память и профиль
  ✅ Голосовое управление
  ✅ Анализ данных (CSV/JSON)
  ✅ Скриншоты экрана
  ✅ Запуск приложений
        """
    )

    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "llama3.1"),
        help="Модель Ollama (по умолчанию: llama3.1)"
    )

    parser.add_argument(
        "--profile",
        default="profile.yaml",
        help="Путь к файлу профиля (по умолчанию: profile.yaml)"
    )

    parser.add_argument(
        "--voice",
        action="store_true",
        help="Включить голосовой режим"
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
    agent = GodAgent(
        model=args.model,
        profile_file=args.profile,
        voice_mode=args.voice,
        voice_engine=args.engine,
        voice_language=args.language,
    )

    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n\n👋 Прервано пользователем.")
        sys.exit(0)


if __name__ == "__main__":
    main()
