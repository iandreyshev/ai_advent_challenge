# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of daily AI/LLM challenge labs (AI Advent Challenge). Each `AIAdventChallengeDay{N}/` directory is an independent project demonstrating different AI integration patterns. The projects are not interconnected.

## Project Types by Day

**iOS Chat Apps (Days 1-11)**: Swift/SwiftUI apps with ChatGPT API integration
- Xcode projects with `.xcodeproj` structure
- Main code in `AIAdventChallengeDay{N}/AIAdventChallengeDay{N}/ContentView.swift`
- API keys stored in `Secrets.swift` (gitignored)

**Kotlin MCP Servers (Days 12-15, 18, 21-23)**: Model Context Protocol servers using Ktor
- Build/run with Gradle: `./gradlew run`, `./gradlew build`, `./gradlew test`
- Source in `src/main/kotlin/`
- Key files: `Application.kt`, `MCPServer.kt`, `Routing.kt`

**Python RAG Systems (Days 16-17, 19-20)**: Retrieval-Augmented Generation implementations
- Run scripts directly: `python3 build_index.py`, `python3 rag_agent.py`
- Uses Ollama for local embeddings (`nomic-embed-text` model)
- Day 20 uses Makefile: `make index`, `make assistant`

**Bash Automation (Day 24)**: Mobile app release automation script
- Run: `./run.sh -v <version> -n "<notes>" -m "<market>" -a "<app>"`
- Merges release branches, posts to Rocket.Chat, creates YouTrack links
- Handles App Store, Google Play, AppGallery, RuStore releases
- Requires env vars: `RC_RELEASE_BOT_ID`, `RC_RELEASE_BOT_AUTH_TOKEN`, `RC_RECEIVER_ID`

**Python Chat (Days 25-27)**: Ollama chat clients
- Day 25: Simple local chat — `python3 chat.py [model_name]`
- Days 26-27: Remote Ollama on VPS — `python3 chat.py` or `python3 chat.py --host <ip> --model <model>`
- Days 26-27 use `.env` for config (`OLLAMA_HOST`, `OLLAMA_PORT`, `OLLAMA_MODEL`)
- Chat commands: `exit`/`quit`, `clear`, `model <name>`

**Python LLM Optimization (Day 28)**: Local LLM parameter tuning and prompt engineering
- Run: `python3 optimize_llm.py` (interactive demo)
- Run: `python3 benchmark.py` (benchmarks with metrics)
- Demonstrates: temperature, top_p, num_ctx, prompt templates comparison

**Python Data Analyst (Day 29)**: Local data analysis with Ollama
- Run: `python3 analyst.py <data_file> [model]`
- Loads CSV/JSON, builds statistical summary, answers analytical questions
- Sample data in `sample_data/` (server logs, user funnel)

**Python Personal Agent (Day 30)**: Personalized AI agent with memory
- Run: `python3 agent.py [--profile path] [--model name] [--no-auto-memory]`
- Loads user profile from `profile.yaml` (name, role, habits, projects, preferences)
- Persistent memory between sessions (`memory.json`, gitignored)
- Facts rephrased in third person via LLM before saving
- Auto-extracts facts from user messages; manual `/remember <fact>` command
- Commands: `/profile`, `/remember`, `/memory`, `/forget`, `/clear`, `/model`, `/help`
- Requires: `pyyaml`

**Python Voice Agent (Day 31)**: Voice-controlled AI agent with speech recognition
- Run: `python3 voice_agent.py [--model name] [--engine google|sphinx|whisper] [--language ru-RU]`
- Architecture: Speech → Text (Speech Recognition) → LLM (Ollama) → Text output
- Supports multiple recognition engines: Google (online), Sphinx (offline), Whisper API
- Continuous conversation loop with voice commands (continues listening after each command)
- Screenshot feature: say "скриншот" or "screenshot" to capture screen (saved to `screenshots/` folder)
- App launcher: say "просыпайся" or "папочка вернулся" to launch workspace apps (Chrome, VS Code, Fork, Android Studio, Terminal)
- Cross-platform support: macOS, Windows, Linux
- Demo mode: `python3 demo.py` (single shot for video recording)
- Test mode: `python3 test_agent.py` (no microphone), `python3 test_microphone.py` (mic check)
- Makefile commands: `make install`, `make run`, `make demo`, `make test`, `make test-mic`
- Requires: `SpeechRecognition`, `PyAudio`, `Pillow`, `requests` (plus `portaudio` system library)
- Optional: `pocketsphinx` for offline mode, `OPENAI_API_KEY` for Whisper

## Common Dependencies

**Ollama** (required for most Python/Kotlin projects):
```bash
brew install ollama  # macOS
ollama pull nomic-embed-text
ollama pull qwen2.5
ollama serve
```

**Kotlin projects**: JDK 11+, Gradle wrapper included

**Python projects**: Python 3.8+ (Day 20 requires `pip install -r requirements.txt`)

## Key Patterns

- MCP servers expose tools via HTTP endpoints for LLM integration
- RAG systems: document chunking → embeddings → vector search → LLM generation
- Cosine similarity for semantic search
- Local-first approach (Ollama) with optional cloud fallbacks (Yandex Cloud, Claude API)

## Secrets Handling

- All `*Secrets.*` files are gitignored
- iOS: `Secrets.swift` with API keys
- Python: `.env` files with `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `YANDEX_API_KEY`
- Kotlin: Various secret files in `utils/`
