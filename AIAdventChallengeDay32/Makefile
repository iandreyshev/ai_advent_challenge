.PHONY: help install run voice demo test clean

help:
	@echo "God Agent — Универсальный персональный AI-ассистент"
	@echo ""
	@echo "Команды:"
	@echo "  make install     Установить зависимости"
	@echo "  make run         Запустить в текстовом режиме"
	@echo "  make voice       Запустить в голосовом режиме"
	@echo "  make demo        Демо-режим с примерами"
	@echo "  make test        Тестовый запуск"
	@echo "  make clean       Очистить временные файлы"

install:
	@echo "📦 Установка зависимостей..."
	pip3 install -r requirements.txt
	@echo "✅ Готово!"
	@echo ""
	@echo "Также установите Ollama:"
	@echo "  macOS:   brew install ollama"
	@echo "  Linux:   curl -fsSL https://ollama.com/install.sh | sh"
	@echo ""
	@echo "Затем запустите модель:"
	@echo "  ollama pull qwen2.5"
	@echo "  ollama serve"

run:
	@echo "⚡️ Запуск God Agent (текстовый режим)..."
	python3 god_agent.py

voice:
	@echo "🎤 Запуск God Agent (голосовой режим)..."
	python3 god_agent.py --voice

demo:
	@echo "🎬 Демонстрация возможностей God Agent..."
	python3 god_agent.py --model qwen2.5

test:
	@echo "🧪 Тестовый запуск..."
	python3 -c "from tools import *; print('✅ Все модули загружены успешно')"

clean:
	@echo "🧹 Очистка временных файлов..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Готово!"
