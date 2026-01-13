"""RAG configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class RAGConfig:
    """Configuration for RAG system."""

    # API Keys
    VOYAGE_API_KEY: str = os.getenv('VOYAGE_API_KEY', '')
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')

    # Chunking settings
    CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '500'))
    CHUNK_OVERLAP: int = int(os.getenv('CHUNK_OVERLAP', '50'))

    # Retrieval settings
    TOP_K_RESULTS: int = int(os.getenv('TOP_K_RESULTS', '5'))

    # ChromaDB settings
    CHROMA_PERSIST_DIR: Path = Path(os.getenv('CHROMA_PERSIST_DIR', './data/chromadb'))
    COLLECTION_NAME: str = os.getenv('COLLECTION_NAME', 'project_docs')

    # Paths
    DOCS_PATH: Path = Path(os.getenv('DOCS_PATH', './docs'))
    PROJECT_ROOT: Path = Path(os.getenv('PROJECT_ROOT', '.'))

    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        if not cls.VOYAGE_API_KEY:
            print("Warning: VOYAGE_API_KEY not set, embeddings will not work")
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        # Create directories
        cls.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
