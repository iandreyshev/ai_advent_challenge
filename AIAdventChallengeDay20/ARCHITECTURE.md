# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Assistant                     │
└─────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
        ┌─────────────┐ ┌─────────┐ ┌──────────┐
        │     RAG     │ │   MCP   │ │  Claude  │
        │   System    │ │ Server  │ │    API   │
        └─────────────┘ └─────────┘ └──────────┘
                 │            │
                 │            │
                 ▼            ▼
        ┌─────────────┐ ┌─────────┐
        │  ChromaDB   │ │   Git   │
        │   Vector    │ │  Repo   │
        │     DB      │ │         │
        └─────────────┘ └─────────┘
```

## RAG System

### Document Indexing Flow

```
1. Read Documents
   └─> docs/*.md, README.md

2. Chunk Documents
   └─> Split into 500-token chunks with 50-token overlap

3. Generate Embeddings
   └─> Voyage AI (or fallback)

4. Store in ChromaDB
   └─> Vector database with metadata
```

### Retrieval Flow

```
1. User Query
   └─> "How does authentication work?"

2. Generate Query Embedding
   └─> Voyage AI embedding

3. Semantic Search
   └─> ChromaDB similarity search (top-k=5)

4. Format Context
   └─> Concatenate relevant chunks

5. Send to Claude
   └─> With RAG context + Git context

6. Return Answer
   └─> Formatted response with sources
```

## MCP Server

### Git Integration

The MCP (Model Context Protocol) server provides:

```python
# Available Tools
- get_current_branch()    # Current branch info
- get_git_status()        # Modified/staged files
- get_recent_commits()    # Commit history
- get_file_history()      # File-specific history
- get_branches()          # All branches
- get_remote_info()       # Remote repositories
- get_diff()              # Git diff output
```

### Context Flow

```
1. MCP Server initializes with repo path
2. Monitors git repository state
3. Provides context to Assistant
4. Context included in every query:
   - Current branch
   - Recent commits
   - File status
   - Remote info
```

## Claude Integration

### Prompt Structure

```
System Prompt:
  - Role definition
  - Available tools (RAG + MCP)
  - Output guidelines

User Message:
  - Original question
  - Git context (from MCP)
  - RAG context (relevant docs)

Response:
  - Answer based on context
  - Source citations
  - Code examples
```

### API Call

```python
client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=2000,
    system=system_prompt,
    messages=[{
        "role": "user",
        "content": f"""
        Question: {query}

        Git Context: {git_context}

        Documentation: {rag_context}
        """
    }]
)
```

## Data Flow

### Complete Request Flow

```
1. User Input
   │
   ├─> "How does auth work?"
   │
2. Document Retrieval (RAG)
   │
   ├─> Query embedding
   ├─> Vector search in ChromaDB
   └─> Get relevant docs (API.md, STYLE_GUIDE.md)
   │
3. Git Context (MCP)
   │
   ├─> Current branch: main
   ├─> Recent commits
   └─> Status
   │
4. Build Prompt
   │
   ├─> System: You are a dev assistant...
   ├─> User query
   ├─> Git context
   └─> RAG results
   │
5. Claude API Call
   │
   └─> Generate response
   │
6. Format Output
   │
   └─> Markdown with sources
```

## File Structure

```
rag-assistant/
│
├── src/
│   ├── rag/                    # RAG System
│   │   ├── config.py          # Configuration
│   │   ├── embeddings.py      # Embedding generation
│   │   ├── chunker.py         # Document chunking
│   │   ├── indexer.py         # Document indexing
│   │   └── retriever.py       # Document retrieval
│   │
│   ├── mcp/                    # MCP Server
│   │   ├── git_tools.py       # Git operations
│   │   └── server.py          # MCP server
│   │
│   └── assistant/              # AI Assistant
│       ├── assistant.py       # Main assistant logic
│       ├── cli.py             # CLI interface
│       └── __main__.py        # Entry point
│
├── docs/                       # Documentation (indexed)
│   ├── API.md
│   ├── STYLE_GUIDE.md
│   ├── DATABASE_SCHEMA.md
│   ├── USAGE.md
│   └── EXAMPLES.md
│
├── data/                       # Runtime data
│   └── chromadb/              # Vector DB storage
│
├── requirements.txt            # Dependencies
├── .env                        # Configuration
├── Makefile                    # Shortcuts
├── setup.sh                    # Setup script
└── test_system.py             # Tests
```

## Key Technologies

### RAG Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Vector DB | ChromaDB | Store embeddings |
| Embeddings | Voyage AI | Text → vectors |
| Chunking | Custom | Split documents |
| Retrieval | Similarity search | Find relevant docs |

### MCP Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Git integration | GitPython | Read repo state |
| Protocol | Custom MCP | Provide context |
| Tools | Python functions | Expose git info |

### AI Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM | Claude Opus 4.5 | Answer questions |
| API | Anthropic SDK | Make API calls |
| CLI | Click + Rich | User interface |

## Scalability Considerations

### For Production

1. **Vector DB**: Consider Pinecone/Weaviate for larger scale
2. **Embeddings**: Batch processing for large docs
3. **Caching**: Cache frequent queries
4. **Rate limiting**: Add API rate limiting
5. **Error handling**: Comprehensive error recovery
6. **Monitoring**: Add logging and metrics
7. **Authentication**: Add user auth for multi-user

### Performance Optimization

- Use prompt caching for system prompts
- Batch embed multiple documents
- Index incrementally (only changed files)
- Cache embeddings
- Optimize chunk size for your docs
