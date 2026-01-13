"""Document indexing with vector database."""

from typing import List, Dict, Optional
from pathlib import Path

# Try to import ChromaDB, fallback to simple implementation
try:
    import chromadb
    from chromadb.config import Settings
    USE_CHROMADB = True
except Exception as e:
    print(f"ChromaDB not available ({e}), using simple fallback vector DB")
    from .simple_vectordb import PersistentClient
    USE_CHROMADB = False

from .config import RAGConfig
from .embeddings import EmbeddingGenerator
from .chunker import DocumentChunker


class DocumentIndexer:
    """Index documents into vector database."""

    def __init__(
        self,
        collection_name: str = RAGConfig.COLLECTION_NAME,
        persist_directory: Path = RAGConfig.CHROMA_PERSIST_DIR
    ):
        """
        Initialize document indexer.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Initialize vector DB (ChromaDB or fallback)
        if USE_CHROMADB:
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = PersistentClient(
                path=str(persist_directory)
            )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Project documentation and code"}
        )

        # Initialize components
        self.embedder = EmbeddingGenerator()
        self.chunker = DocumentChunker()

    def index_directory(
        self,
        directory: Path,
        extensions: Optional[List[str]] = None
    ) -> int:
        """
        Index all documents in a directory.

        Args:
            directory: Directory to index
            extensions: File extensions to include

        Returns:
            Number of chunks indexed
        """
        print(f"Indexing directory: {directory}")

        # Chunk all files
        chunks = self.chunker.chunk_directory(directory, extensions)
        print(f"Created {len(chunks)} chunks")

        if not chunks:
            print("No chunks to index")
            return 0

        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedder.generate(texts)

        # Prepare data for vector DB
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [chunk['metadata'] for chunk in chunks]

        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        print(f"Indexed {len(chunks)} chunks successfully")
        return len(chunks)

    def index_text(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Index a single text document.

        Args:
            text: Text to index
            metadata: Optional metadata
            doc_id: Optional document ID

        Returns:
            Document ID
        """
        # Chunk the text
        chunks = self.chunker.chunk_text(text, metadata)

        if not chunks:
            raise ValueError("No chunks created from text")

        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedder.generate(texts)

        # Generate IDs
        base_id = doc_id or f"doc_{hash(text)}"
        ids = [f"{base_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [chunk['metadata'] for chunk in chunks]

        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        return base_id

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate collection
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Project documentation and code"}
        )
        print(f"Cleared collection: {self.collection_name}")

    def get_stats(self) -> Dict:
        """
        Get collection statistics.

        Returns:
            Dictionary with collection stats
        """
        count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'document_count': count,
            'persist_directory': str(self.persist_directory)
        }
