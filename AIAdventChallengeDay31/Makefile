.PHONY: install install-direct run run-direct run-direct-local run-en run-offline demo test test-mic help clean

# Определяем Python (используем venv если существует)
PYTHON := $(shell if [ -d "venv" ]; then echo "venv/bin/python"; else echo "python3"; fi)
PIP := $(shell if [ -d "venv" ]; then echo "venv/bin/pip"; else echo "pip3"; fi)

# Установка зависимостей
install:
	@echo "📦 Установка зависимостей..."
	@if [ ! -d "venv" ]; then \
		echo "📦 Создание виртуального окружения..."; \
		python3 -m venv venv; \
	fi
	@$(PIP) install -r requirements.txt
	@echo "✅ Готово!"

# Установка зависимостей для прямой версии
install-direct:
	@echo "📦 Установка зависимостей для прямой версии..."
	@if [ ! -d "venv" ]; then \
		echo "📦 Создание виртуального окружения..."; \
		python3 -m venv venv; \
	fi
	@$(PIP) install -r requirements-direct.txt
	@echo "✅ Готово!"

# Запуск голосового агента
run:
	@echo "🎙️  Запуск голосового агента..."
	@$(PYTHON) voice_agent.py

# Запуск прямой версии с OpenAI Whisper API
run-direct:
	@echo "🎙️  Запуск прямой версии (OpenAI Whisper API)..."
	@$(PYTHON) voice_agent_direct.py --mode api

# Запуск прямой версии с локальным Whisper
run-direct-local:
	@echo "🎙️  Запуск прямой версии (локальный Whisper)..."
	@$(PYTHON) voice_agent_direct.py --mode local

# Демонстрационный режим (один запрос)
demo:
	@echo "🎬 Демонстрационный режим..."
	@$(PYTHON) demo.py

# Тестирование без микрофона
test:
	@echo "🧪 Запуск тестов..."
	@$(PYTHON) test_agent.py

# Проверка микрофона
test-mic:
	@echo "🔍 Проверка микрофона..."
	@$(PYTHON) test_microphone.py

# Запуск с английским языком
run-en:
	@echo "🎙️  Запуск с английским языком..."
	@$(PYTHON) voice_agent.py --language en-US

# Запуск в офлайн режиме (Sphinx)
run-offline:
	@echo "🎙️  Запуск в офлайн режиме..."
	@$(PIP) install pocketsphinx
	@$(PYTHON) voice_agent.py --engine sphinx

# Очистка временных файлов
clean:
	@echo "🧹 Очистка..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✅ Готово!"

# Справка
help:
	@echo "📖 Доступные команды:"
	@echo ""
	@echo "Установка:"
	@echo "  make install           - Установить зависимости (базовая версия)"
	@echo "  make install-direct    - Установить зависимости (прямая версия)"
	@echo ""
	@echo "Запуск:"
	@echo "  make run               - Запустить голосовой агент (базовая версия)"
	@echo "  make run-direct        - Прямая версия с OpenAI Whisper API"
	@echo "  make run-direct-local  - Прямая версия с локальным Whisper"
	@echo "  make demo              - Демонстрационный режим (1 запрос)"
	@echo ""
	@echo "Тестирование:"
	@echo "  make test              - Тестирование без микрофона"
	@echo "  make test-mic          - Проверить микрофон"
	@echo ""
	@echo "Дополнительно:"
	@echo "  make run-en            - Запуск с английским языком"
	@echo "  make run-offline       - Запуск в офлайн режиме (Sphinx)"
	@echo "  make clean             - Очистить временные файлы"
	@echo "  make help              - Показать эту справку"
