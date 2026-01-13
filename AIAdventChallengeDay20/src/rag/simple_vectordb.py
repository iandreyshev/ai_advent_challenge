"""Simple in-memory vector database fallback for ChromaDB."""

from typing import List, Dict, Any, Optional
import json
import pickle
from pathlib import Path
import numpy as np


class SimpleVectorDB:
    """
    Simple in-memory vector database.
    Fallback when ChromaDB doesn't work (Python 3.14+).
    """

    def __init__(self, persist_directory: Path, collection_name: str):
        """
        Initialize simple vector DB.

        Args:
            persist_directory: Directory to save data
            collection_name: Collection name
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.collection_name = collection_name
        self.db_file = self.persist_directory / f"{collection_name}.json"

        # In-memory storage
        self.documents: List[str] = []
        self.embeddings: List[List[float]] = []
        self.metadatas: List[Dict] = []
        self.ids: List[str] = []

        # Load existing data
        self._load()

    def add(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> None:
        """
        Add documents to collection.

        Args:
            embeddings: List of embeddings
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of IDs
        """
        self.embeddings.extend(embeddings)
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)

        self._save()

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query similar documents.

        Args:
            query_embeddings: Query embedding vectors
            n_results: Number of results
            where: Metadata filter (optional)

        Returns:
            Query results
        """
        if not self.embeddings:
            return {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]],
                'ids': [[]]
            }

        query_embedding = query_embeddings[0]

        # Calculate cosine similarities
        similarities = []
        for idx, doc_embedding in enumerate(self.embeddings):
            # Filter by metadata if provided
            if where:
                match = all(
                    self.metadatas[idx].get(key) == value
                    for key, value in where.items()
                )
                if not match:
                    continue

            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((idx, similarity))

        # Sort by similarity (higher is better)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Get top N results
        top_indices = [idx for idx, _ in similarities[:n_results]]

        # Format results
        results = {
            'documents': [[self.documents[idx] for idx in top_indices]],
            'metadatas': [[self.metadatas[idx] for idx in top_indices]],
            'distances': [[1.0 - sim for _, sim in similarities[:n_results]]],  # Convert to distance
            'ids': [[self.ids[idx] for idx in top_indices]]
        }

        return results

    def count(self) -> int:
        """Get number of documents."""
        return len(self.documents)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        # Convert to numpy for easier calculation
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _save(self) -> None:
        """Save data to disk."""
        data = {
            'documents': self.documents,
            'embeddings': self.embeddings,
            'metadatas': self.metadatas,
            'ids': self.ids
        }

        with open(self.db_file, 'w') as f:
            json.dump(data, f)

    def _load(self) -> None:
        """Load data from disk."""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)

                self.documents = data.get('documents', [])
                self.embeddings = data.get('embeddings', [])
                self.metadatas = data.get('metadatas', [])
                self.ids = data.get('ids', [])
            except Exception as e:
                print(f"Warning: Could not load existing data: {e}")


class SimpleVectorDBClient:
    """Client wrapper for SimpleVectorDB."""

    def __init__(self, path: str, settings=None):
        """Initialize client."""
        self.path = Path(path)
        self.collections: Dict[str, SimpleVectorDB] = {}

    def get_or_create_collection(self, name: str, metadata=None) -> SimpleVectorDB:
        """Get or create collection."""
        if name not in self.collections:
            self.collections[name] = SimpleVectorDB(
                persist_directory=self.path,
                collection_name=name
            )
        return self.collections[name]

    def get_collection(self, name: str) -> SimpleVectorDB:
        """Get existing collection."""
        if name not in self.collections:
            # Try to load from disk
            db = SimpleVectorDB(
                persist_directory=self.path,
                collection_name=name
            )
            if db.count() > 0:
                self.collections[name] = db
            else:
                raise ValueError(f"Collection '{name}' not found")

        return self.collections[name]

    def delete_collection(self, name: str) -> None:
        """Delete collection."""
        if name in self.collections:
            del self.collections[name]

        # Delete file
        db_file = self.path / f"{name}.json"
        if db_file.exists():
            db_file.unlink()


def PersistentClient(path: str, settings=None):
    """Factory function to match ChromaDB API."""
    return SimpleVectorDBClient(path, settings)
