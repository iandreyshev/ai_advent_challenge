"""Embedding generation for documents."""

from typing import List, Optional
import voyageai
from .config import RAGConfig


class EmbeddingGenerator:
    """Generate embeddings for text using Voyage AI."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize embedding generator.

        Args:
            api_key: Voyage AI API key. If None, uses config.
        """
        self.api_key = api_key or RAGConfig.VOYAGE_API_KEY
        if self.api_key:
            self.client = voyageai.Client(api_key=self.api_key)
        else:
            self.client = None
            print("Warning: No Voyage API key provided. Using fallback embeddings.")

    def generate(self, texts: List[str], model: str = "voyage-2") -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            model: Voyage AI model name

        Returns:
            List of embedding vectors
        """
        if self.client:
            try:
                result = self.client.embed(
                    texts=texts,
                    model=model,
                    input_type="document"
                )
                return result.embeddings
            except Exception as e:
                print(f"Error generating embeddings: {e}")
                return self._fallback_embeddings(texts)
        else:
            return self._fallback_embeddings(texts)

    def generate_query_embedding(
        self,
        query: str,
        model: str = "voyage-2"
    ) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Query text
            model: Voyage AI model name

        Returns:
            Embedding vector
        """
        if self.client:
            try:
                result = self.client.embed(
                    texts=[query],
                    model=model,
                    input_type="query"
                )
                return result.embeddings[0]
            except Exception as e:
                print(f"Error generating query embedding: {e}")
                return self._fallback_embeddings([query])[0]
        else:
            return self._fallback_embeddings([query])[0]

    @staticmethod
    def _fallback_embeddings(texts: List[str]) -> List[List[float]]:
        """
        Fallback simple embeddings when API is unavailable.

        Args:
            texts: List of texts

        Returns:
            Simple hash-based embeddings
        """
        # Simple hash-based fallback (not for production!)
        embeddings = []
        for text in texts:
            # Create a simple 384-dimensional embedding based on text hash
            hash_val = hash(text)
            embedding = [
                float((hash_val + i) % 1000) / 1000.0
                for i in range(384)
            ]
            embeddings.append(embedding)
        return embeddings
