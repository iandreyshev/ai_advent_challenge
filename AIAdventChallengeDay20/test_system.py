#!/usr/bin/env python3
"""Test script to verify RAG system without API keys."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from src.rag.config import RAGConfig
        from src.rag.embeddings import EmbeddingGenerator
        from src.rag.chunker import DocumentChunker
        from src.rag.indexer import DocumentIndexer
        from src.mcp.git_tools import GitTools
        from src.mcp.server import MCPServer
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_chunker():
    """Test document chunking."""
    print("\nTesting document chunker...")
    try:
        from src.rag.chunker import DocumentChunker

        chunker = DocumentChunker(chunk_size=10, chunk_overlap=2)
        text = "This is a test document with multiple words to test chunking functionality."
        chunks = chunker.chunk_text(text)

        print(f"✓ Created {len(chunks)} chunks from text")
        print(f"  First chunk: {chunks[0]['text'][:50]}...")
        return True
    except Exception as e:
        print(f"✗ Chunker test failed: {e}")
        return False

def test_git_tools():
    """Test git integration."""
    print("\nTesting git tools...")
    try:
        from src.mcp.git_tools import GitTools

        git = GitTools()
        branch = git.get_current_branch()

        if 'error' in branch:
            print(f"⚠ Not a git repo: {branch['error']}")
        else:
            print(f"✓ Current branch: {branch.get('name', 'N/A')}")

        status = git.get_status()
        if 'error' not in status:
            print(f"✓ Status: {len(status.get('modified', []))} modified files")

        return True
    except Exception as e:
        print(f"✗ Git tools test failed: {e}")
        return False

def test_mcp_server():
    """Test MCP server."""
    print("\nTesting MCP server...")
    try:
        from src.mcp.server import MCPServer

        mcp = MCPServer()
        tools = mcp.list_tools()

        print(f"✓ MCP server initialized")
        print(f"✓ Available tools: {len(tools)}")
        for tool in tools[:3]:
            print(f"  - {tool['name']}")

        context = mcp.get_context()
        print(f"✓ Got git context")

        return True
    except Exception as e:
        print(f"✗ MCP server test failed: {e}")
        return False

def test_embeddings():
    """Test embedding generation (fallback mode)."""
    print("\nTesting embeddings (fallback mode)...")
    try:
        from src.rag.embeddings import EmbeddingGenerator

        embedder = EmbeddingGenerator(api_key=None)  # Force fallback
        texts = ["Hello world", "Test document"]
        embeddings = embedder.generate(texts)

        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ Embedding dimension: {len(embeddings[0])}")
        return True
    except Exception as e:
        print(f"✗ Embeddings test failed: {e}")
        return False

def test_directory_structure():
    """Test that all required directories exist."""
    print("\nTesting directory structure...")
    required_dirs = [
        "src/rag",
        "src/mcp",
        "src/assistant",
        "docs"
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ not found")
            all_exist = False

    return all_exist

def test_documentation():
    """Test that documentation files exist."""
    print("\nTesting documentation...")
    required_docs = [
        "README.md",
        "docs/API.md",
        "docs/STYLE_GUIDE.md",
        "docs/DATABASE_SCHEMA.md",
        "docs/USAGE.md",
        "docs/EXAMPLES.md"
    ]

    all_exist = True
    for doc_path in required_docs:
        path = Path(doc_path)
        if path.exists():
            size = path.stat().st_size
            print(f"✓ {doc_path} ({size} bytes)")
        else:
            print(f"✗ {doc_path} not found")
            all_exist = False

    return all_exist

def main():
    """Run all tests."""
    print("=" * 60)
    print("RAG Development Assistant - System Test")
    print("=" * 60)

    results = []

    results.append(("Directory Structure", test_directory_structure()))
    results.append(("Documentation", test_documentation()))
    results.append(("Imports", test_imports()))
    results.append(("Document Chunker", test_chunker()))
    results.append(("Git Tools", test_git_tools()))
    results.append(("MCP Server", test_mcp_server()))
    results.append(("Embeddings (Fallback)", test_embeddings()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Add API keys to .env file")
        print("2. Run: make index")
        print("3. Run: make assistant")
        return 0
    else:
        print("\n⚠ Some tests failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
