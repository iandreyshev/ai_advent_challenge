#!/bin/bash
# Скрипт установки зависимостей для голосового агента

set -e

echo "🚀 Установка голосового агента (Day 31)"
echo "========================================"
echo ""

# Проверка Python
echo "🔍 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION найден"
echo ""

# Проверка pip
echo "🔍 Проверка pip..."
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip не найден. Установите pip"
    exit 1
fi
echo "✅ pip найден"
echo ""

# Определение ОС
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "🖥️  Операционная система: $MACHINE"
echo ""

# Установка PortAudio
echo "📦 Установка PortAudio..."
if [ "$MACHINE" == "Mac" ]; then
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew не найден. Установите Homebrew для установки PortAudio"
        echo "   https://brew.sh"
        exit 1
    fi

    if brew list portaudio &> /dev/null; then
        echo "✅ PortAudio уже установлен"
    else
        echo "   Установка через Homebrew..."
        brew install portaudio
        echo "✅ PortAudio установлен"
    fi
elif [ "$MACHINE" == "Linux" ]; then
    echo "   Установка через apt (требуется sudo)..."
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-pyaudio
    echo "✅ PortAudio установлен"
else
    echo "⚠️  Автоматическая установка PortAudio не поддерживается для $MACHINE"
    echo "   Установите PortAudio вручную"
fi
echo ""

# Установка Python пакетов
echo "📦 Установка Python зависимостей..."
pip3 install -r requirements.txt
echo "✅ Python зависимости установлены"
echo ""

# Проверка Ollama
echo "🔍 Проверка Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama не найден"
    echo ""
    echo "Для работы агента требуется Ollama."
    echo "Установите Ollama:"
    echo "  macOS:  brew install ollama"
    echo "  Linux:  curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo "После установки запустите:"
    echo "  ollama serve"
    echo "  ollama pull qwen2.5"
else
    echo "✅ Ollama найден"

    # Проверка запущен ли Ollama
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo "✅ Ollama запущен"

        # Проверка модели
        if ollama list | grep -q "qwen2.5"; then
            echo "✅ Модель qwen2.5 установлена"
        else
            echo "⚠️  Модель qwen2.5 не найдена"
            echo "   Загрузка модели..."
            ollama pull qwen2.5
            echo "✅ Модель qwen2.5 загружена"
        fi
    else
        echo "⚠️  Ollama не запущен"
        echo "   Запустите: ollama serve"
    fi
fi
echo ""

# Создание .env из примера
if [ ! -f ".env" ]; then
    echo "📝 Создание файла .env..."
    cp .env.example .env
    echo "✅ Файл .env создан"
    echo "   Отредактируйте .env при необходимости"
else
    echo "✅ Файл .env уже существует"
fi
echo ""

# Проверка микрофона
echo "🎤 Проверка микрофона..."
echo "   Запускаем тест микрофона..."
python3 test_microphone.py

echo ""
echo "========================================"
echo "✅ Установка завершена!"
echo "========================================"
echo ""
echo "Для запуска:"
echo "  python3 voice_agent.py"
echo ""
echo "Или используйте Makefile:"
echo "  make run       - Запуск агента"
echo "  make demo      - Демонстрация"
echo "  make test      - Тестирование"
echo "  make help      - Справка"
echo ""
