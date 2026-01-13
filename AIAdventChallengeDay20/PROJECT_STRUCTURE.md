# Project Structure

```
AIAdventChallengeDay20/
│
├── 📄 README.md                    # Main project documentation
├── 📄 QUICKSTART.md               # Quick start guide
├── 📄 ARCHITECTURE.md             # System architecture
├── 📄 PROJECT_STRUCTURE.md        # This file
│
├── ⚙️  .env.example                # Environment variables template
├── ⚙️  .gitignore                  # Git ignore rules
├── ⚙️  requirements.txt            # Python dependencies
├── ⚙️  Makefile                    # Build commands
├── 🔧 setup.sh                    # Setup script
├── 🧪 test_system.py              # System tests
│
├── 📚 docs/                        # Documentation (indexed by RAG)
│   ├── API.md                     # API endpoints documentation
│   ├── STYLE_GUIDE.md             # Code style guidelines
│   ├── DATABASE_SCHEMA.md         # Database schema
│   ├── USAGE.md                   # Usage instructions
│   └── EXAMPLES.md                # Usage examples
│
└── 📦 src/                         # Source code
    │
    ├── 🤖 assistant/               # AI Assistant
    │   ├── __init__.py
    │   ├── __main__.py            # Entry point
    │   ├── assistant.py           # Main assistant logic
    │   └── cli.py                 # CLI interface
    │
    ├── 🔍 rag/                     # RAG System
    │   ├── __init__.py
    │   ├── config.py              # Configuration
    │   ├── embeddings.py          # Embedding generation
    │   ├── chunker.py             # Document chunking
    │   ├── indexer.py             # Document indexing
    │   └── retriever.py           # Document retrieval
    │
    └── 🔌 mcp/                     # MCP Server
        ├── __init__.py
        ├── git_tools.py           # Git operations
        └── server.py              # MCP server implementation
```

## File Descriptions

### Root Files

| File | Lines | Description |
|------|-------|-------------|
| `README.md` | ~100 | Main project documentation and overview |
| `QUICKSTART.md` | ~80 | Quick start guide for new users |
| `ARCHITECTURE.md` | ~300 | Detailed system architecture |
| `requirements.txt` | 18 | Python package dependencies |
| `Makefile` | 35 | Convenient build commands |
| `setup.sh` | 40 | Automated setup script |
| `test_system.py` | ~180 | System verification tests |

### Documentation Files

| File | Size | Purpose |
|------|------|---------|
| `docs/API.md` | 2.4KB | REST API endpoints and examples |
| `docs/STYLE_GUIDE.md` | 4.4KB | Python coding standards |
| `docs/DATABASE_SCHEMA.md` | 3.4KB | Database tables and relationships |
| `docs/USAGE.md` | 1.6KB | Command usage instructions |
| `docs/EXAMPLES.md` | 4.5KB | Real usage examples |

### Source Code

#### Assistant Module (`src/assistant/`)

| File | Purpose |
|------|---------|
| `assistant.py` | Core assistant logic with RAG and MCP integration |
| `cli.py` | Click-based CLI with Rich formatting |
| `__main__.py` | Module entry point |

**Key Classes:**
- `DevelopmentAssistant`: Main assistant class
  - `help()`: Answer project questions
  - `search_docs()`: Search documentation
  - `get_git_context()`: Get git information

**Key Commands:**
- `help [query]`: Get help
- `search <query>`: Search docs
- `files <query>`: Find related files
- `git`: Show git context
- `interactive`: Start interactive session
- `index`: Index documentation

#### RAG Module (`src/rag/`)

| File | Purpose |
|------|---------|
| `config.py` | RAG configuration and settings |
| `embeddings.py` | Voyage AI embedding generation |
| `chunker.py` | Document splitting and chunking |
| `indexer.py` | ChromaDB indexing |
| `retriever.py` | Semantic search and retrieval |

**Key Classes:**
- `RAGConfig`: Configuration management
- `EmbeddingGenerator`: Generate embeddings
- `DocumentChunker`: Split documents
- `DocumentIndexer`: Index to ChromaDB
- `DocumentRetriever`: Search documents

**Configuration:**
- Chunk size: 500 tokens
- Chunk overlap: 50 tokens
- Top-K results: 5
- Vector dimension: 384

#### MCP Module (`src/mcp/`)

| File | Purpose |
|------|---------|
| `git_tools.py` | Git repository operations |
| `server.py` | MCP server implementation |

**Key Classes:**
- `GitTools`: Git operations wrapper
  - `get_current_branch()`
  - `get_status()`
  - `get_recent_commits()`
  - `get_file_history()`
  - `get_diff()`

- `MCPServer`: MCP protocol implementation
  - `list_tools()`: Available tools
  - `call_tool()`: Execute tool
  - `get_context()`: Full git context

## Data Flow

```
User Input
    ↓
┌───────────────┐
│  CLI (Click)  │
└───────────────┘
    ↓
┌─────────────────────────┐
│  DevelopmentAssistant   │
└─────────────────────────┘
    ↓           ↓
    ↓      ┌──────────┐
    ↓      │ MCPServer│
    ↓      └──────────┘
    ↓           ↓
    ↓      ┌──────────┐
    ↓      │GitTools  │
    ↓      └──────────┘
    ↓
┌──────────────────┐
│ DocumentRetriever│
└──────────────────┘
    ↓
┌──────────────────┐
│    ChromaDB      │
└──────────────────┘
    ↓
┌──────────────────┐
│   Claude API     │
└──────────────────┘
    ↓
Formatted Response
```

## Dependencies

### Core Dependencies
- `anthropic>=0.40.0` - Claude API client
- `chromadb>=0.4.22` - Vector database
- `voyageai>=0.2.3` - Embeddings
- `GitPython>=3.1.40` - Git integration

### CLI Dependencies
- `click>=8.1.7` - CLI framework
- `rich>=13.7.0` - Terminal formatting

### MCP Dependencies
- `mcp>=1.0.0` - Model Context Protocol
- `pydantic>=2.5.0` - Data validation
- `fastapi>=0.109.0` - API framework

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
VOYAGE_API_KEY=pa-...  # Will use fallback if not provided

# Configuration
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
CHROMA_PERSIST_DIR=./data/chromadb
COLLECTION_NAME=project_docs
```

## Statistics

- **Total Python files**: 13
- **Total documentation files**: 10
- **Total lines of code**: ~1,500
- **Total documentation**: ~5,000 words
- **Supported file types**: .md, .py, .js, .json, .txt
