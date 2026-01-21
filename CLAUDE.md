# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of 25 daily AI/LLM challenge labs (AI Advent Challenge). Each `AIAdventChallengeDay{N}/` directory is an independent project demonstrating different AI integration patterns. The projects are not interconnected.

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

**Python Chat (Day 25)**: Simple Ollama chat client
- Run: `python3 chat.py [model_name]`

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
