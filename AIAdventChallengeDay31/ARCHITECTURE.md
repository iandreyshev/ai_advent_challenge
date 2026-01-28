# 🏗️ Архитектура голосового агента

## 📐 Общая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     VOICE AGENT SYSTEM                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│              │         │              │         │              │
│  User Voice  │────────▶│  Microphone  │────────▶│  PyAudio     │
│              │         │              │         │              │
└──────────────┘         └──────────────┘         └──────────────┘
                                                          │
                                                          │ Audio Stream
                                                          ▼
                         ┌───────────────────────────────────────┐
                         │     SPEECH RECOGNITION ENGINE         │
                         │  ┌──────────┬──────────┬───────────┐  │
                         │  │  Google  │  Sphinx  │  Whisper  │  │
                         │  │  Speech  │   CMU    │    API    │  │
                         │  │   API    │ (Offline)│ (OpenAI)  │  │
                         │  └──────────┴──────────┴───────────┘  │
                         └───────────────────────────────────────┘
                                          │
                                          │ Text String
                                          ▼
                         ┌───────────────────────────────────────┐
                         │         VOICE AGENT LOGIC             │
                         │  ┌─────────────────────────────────┐  │
                         │  │   • Command Processing          │  │
                         │  │   • Text Cleaning               │  │
                         │  │   • Exit Command Detection      │  │
                         │  └─────────────────────────────────┘  │
                         └───────────────────────────────────────┘
                                          │
                                          │ Cleaned Text
                                          ▼
                         ┌───────────────────────────────────────┐
                         │          OLLAMA LLM SERVER            │
                         │  ┌─────────────────────────────────┐  │
                         │  │  Model: qwen2.5 / llama3.2     │  │
                         │  │  Endpoint: /api/generate        │  │
                         │  │  Port: 11434                    │  │
                         │  └─────────────────────────────────┘  │
                         └───────────────────────────────────────┘
                                          │
                                          │ Response Text
                                          ▼
                         ┌───────────────────────────────────────┐
                         │        CONSOLE OUTPUT                 │
                         │                                       │
                         │    💬 Formatted Text Response         │
                         │                                       │
                         └───────────────────────────────────────┘
```

## 🔄 Последовательность работы

### 1. Инициализация

```
START
  │
  ├─▶ Инициализация SpeechRecognizer
  │   └─▶ Настройка energy_threshold
  │   └─▶ Настройка pause_threshold
  │
  ├─▶ Проверка подключения к Ollama
  │   └─▶ HTTP GET: localhost:11434/api/tags
  │
  └─▶ Вывод приветственного сообщения
```

### 2. Основной цикл (listen → recognize → query → display)

```
LOOP (while True):
  │
  ├─▶ [1] LISTEN
  │   │
  │   ├─▶ Открыть микрофон (sr.Microphone)
  │   │
  │   ├─▶ Калибровка (adjust_for_ambient_noise)
  │   │   └─▶ Анализ фонового шума: 1 сек
  │   │
  │   ├─▶ Захват аудио (recognizer.listen)
  │   │   ├─▶ timeout: 5 сек
  │   │   └─▶ phrase_time_limit: 10 сек
  │   │
  │   └─▶ Возврат: audio_data
  │
  ├─▶ [2] RECOGNIZE
  │   │
  │   ├─▶ IF engine == "google":
  │   │   └─▶ recognize_google(audio, lang="ru-RU")
  │   │       └─▶ HTTP → Google Speech API
  │   │
  │   ├─▶ IF engine == "sphinx":
  │   │   └─▶ recognize_sphinx(audio)
  │   │       └─▶ Локальная обработка (CMU Sphinx)
  │   │
  │   ├─▶ IF engine == "whisper":
  │   │   └─▶ recognize_whisper_api(audio, api_key)
  │   │       └─▶ HTTP → OpenAI Whisper API
  │   │
  │   └─▶ Возврат: text_string
  │
  ├─▶ [3] CHECK EXIT
  │   │
  │   ├─▶ IF text in ["выход", "стоп", "exit", "stop"]:
  │   │   └─▶ BREAK LOOP
  │   │
  │   └─▶ CONTINUE
  │
  ├─▶ [4] QUERY LLM
  │   │
  │   ├─▶ Формирование payload:
  │   │   {
  │   │     "model": "qwen2.5",
  │   │     "prompt": text_string,
  │   │     "stream": false
  │   │   }
  │   │
  │   ├─▶ HTTP POST → localhost:11434/api/generate
  │   │   ├─▶ Timeout: 30 сек
  │   │   └─▶ Headers: {"Content-Type": "application/json"}
  │   │
  │   ├─▶ Парсинг ответа: response.json()
  │   │
  │   └─▶ Возврат: response_text
  │
  └─▶ [5] DISPLAY
      │
      ├─▶ Форматирование вывода:
      │   ┌────────────────────────┐
      │   │ 💬 ОТВЕТ:              │
      │   ├────────────────────────┤
      │   │ {response_text}        │
      │   └────────────────────────┘
      │
      └─▶ LOOP CONTINUE

END
```

## 🧩 Компонентная архитектура

### VoiceAgent Class

```python
VoiceAgent
│
├── __init__(model, host, port, recognition_engine, language)
│   ├── self.model: str
│   ├── self.ollama_url: str
│   ├── self.recognition_engine: str
│   ├── self.language: str
│   └── self.recognizer: sr.Recognizer
│
├── listen() -> Optional[str]
│   ├── Открывает микрофон
│   ├── Калибрует под шум
│   ├── Захватывает аудио
│   └── Вызывает _recognize_speech()
│
├── _recognize_speech(audio) -> str
│   ├── IF engine == "google": recognize_google()
│   ├── IF engine == "sphinx": recognize_sphinx()
│   └── IF engine == "whisper": recognize_whisper_api()
│
├── query_llm(text: str) -> str
│   ├── Формирует HTTP payload
│   ├── Отправляет POST запрос
│   └── Возвращает ответ LLM
│
└── run()
    └── Основной цикл работы
```

## 📊 Диаграмма потоков данных

```
[User Speech]
      │
      │ Audio Waves
      ▼
[Microphone Hardware]
      │
      │ Digital Audio
      ▼
[PyAudio Driver]
      │
      │ Audio Buffer
      ▼
[SpeechRecognition Library]
      │
      │ Audio Processing
      ▼
[Speech Recognition API]
      │  ┌────────────────┐
      │  │ Google API     │
      ├─▶│ Sphinx Engine  │
      │  │ Whisper API    │
      │  └────────────────┘
      │
      │ Plain Text String
      ▼
[VoiceAgent Logic]
      │
      │ Command Processing
      ├─▶ [Exit Check] ──▶ [END]
      │
      │ Cleaned Text
      ▼
[HTTP Request Layer]
      │
      │ JSON Payload
      ▼
[Ollama Server]
      │
      │ LLM Processing
      ▼
[Language Model]
      │
      │ Generated Response
      ▼
[HTTP Response]
      │
      │ JSON Response
      ▼
[VoiceAgent Logic]
      │
      │ Text Formatting
      ▼
[Console Output]
      │
      │ Formatted Display
      ▼
[User Reads]
```

## 🔧 Конфигурационная архитектура

```
┌────────────────────────────────────────────┐
│         CONFIGURATION SOURCES              │
├────────────────────────────────────────────┤
│                                            │
│  1. Environment Variables (.env)           │
│     ├── OLLAMA_MODEL                       │
│     ├── OLLAMA_HOST                        │
│     ├── OLLAMA_PORT                        │
│     └── OPENAI_API_KEY                     │
│                                            │
│  2. CLI Arguments                          │
│     ├── --model                            │
│     ├── --host                             │
│     ├── --port                             │
│     ├── --engine                           │
│     └── --language                         │
│                                            │
│  3. Defaults (in code)                     │
│     ├── model: "qwen2.5"                   │
│     ├── host: "localhost"                  │
│     ├── port: 11434                        │
│     ├── engine: "google"                   │
│     └── language: "ru-RU"                  │
│                                            │
└────────────────────────────────────────────┘
         │
         │ Priority: CLI > ENV > Defaults
         ▼
┌────────────────────────────────────────────┐
│        RUNTIME CONFIGURATION               │
└────────────────────────────────────────────┘
```

## 🌐 Сетевая архитектура

```
┌───────────────┐
│  Voice Agent  │
│  (localhost)  │
└───────┬───────┘
        │
        │ HTTP Requests
        │
        ├─────────────────────┐
        │                     │
        ▼                     ▼
┌───────────────┐    ┌───────────────────┐
│ Ollama Server │    │  Speech API       │
│ localhost:    │    │  (External)       │
│   11434       │    │                   │
└───────────────┘    │  ├─ Google        │
                     │  ├─ OpenAI        │
                     │  └─ (Sphinx: N/A) │
                     └───────────────────┘
```

## 🛡️ Обработка ошибок

```
Error Handling Strategy:

┌─────────────────────────────────────────┐
│  LISTEN PHASE                           │
├─────────────────────────────────────────┤
│  ├─ WaitTimeoutError     → Retry        │
│  ├─ UnknownValueError    → Retry        │
│  ├─ RequestError         → Fatal        │
│  └─ Exception            → Log + Retry  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  RECOGNIZE PHASE                        │
├─────────────────────────────────────────┤
│  ├─ UnknownValueError    → Display Msg  │
│  ├─ RequestError         → Fallback     │
│  └─ Exception            → Log + Retry  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  LLM QUERY PHASE                        │
├─────────────────────────────────────────┤
│  ├─ ConnectionError      → Display Msg  │
│  ├─ Timeout              → Display Msg  │
│  ├─ HTTPError            → Display Msg  │
│  └─ Exception            → Display Msg  │
└─────────────────────────────────────────┘
```

## 📦 Зависимости

```
SYSTEM LEVEL:
├── PortAudio (Audio I/O Library)
└── Ollama (LLM Server)

PYTHON PACKAGES:
├── SpeechRecognition
│   ├── PyAudio (Microphone)
│   └── Requests (HTTP for APIs)
└── requests (Ollama communication)

OPTIONAL:
├── pocketsphinx (Offline recognition)
└── openai-whisper (Better accuracy)
```

## 🎯 Модульность

Система спроектирована модульно:

1. **Capture Module** (PyAudio + Microphone)
   - Независим от распознавания
   - Можно заменить на файловый ввод

2. **Recognition Module** (Speech Recognition)
   - Поддержка множества движков
   - Легко добавить новые

3. **LLM Module** (Ollama Client)
   - Абстрагирован через HTTP API
   - Можно заменить на другой LLM

4. **Output Module** (Console)
   - Простой текстовый вывод
   - Легко заменить на TTS или GUI

## 🔮 Возможности расширения

```
FUTURE EXTENSIONS:

Voice Input Layer:
  ├─ File Input (WAV, MP3)
  ├─ Network Stream
  └─ Phone Call Integration

Recognition Layer:
  ├─ Azure Speech
  ├─ AWS Transcribe
  └─ Local Whisper Model

LLM Layer:
  ├─ Cloud APIs (GPT, Claude)
  ├─ Other Local Models
  └─ RAG Integration

Output Layer:
  ├─ Text-to-Speech
  ├─ GUI Display
  └─ Web Interface
```

---

## 📝 Ключевые проектные решения

1. **Модульность**: Каждый компонент независим
2. **Гибкость**: Множество конфигурационных опций
3. **Отказоустойчивость**: Обработка всех типов ошибок
4. **Производительность**: Локальная LLM для быстрых ответов
5. **Простота**: Минималистичный интерфейс CLI
