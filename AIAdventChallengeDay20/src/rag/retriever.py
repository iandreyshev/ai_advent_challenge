"""Document retrieval from vector database."""

from typing import List, Dict, Optional
from pathlib import Path

# Try to import ChromaDB, fallback to simple implementation
try:
    import chromadb
    from chromadb.config import Settings
    USE_CHROMADB = True
except Exception as e:
    from .simple_vectordb import PersistentClient
    USE_CHROMADB = False

from .config import RAGConfig
from .embeddings import EmbeddingGenerator


class DocumentRetriever:
    """Retrieve relevant documents from vector database."""

    def __init__(
        self,
        collection_name: str = RAGConfig.COLLECTION_NAME,
        persist_directory: Path = RAGConfig.CHROMA_PERSIST_DIR,
        top_k: int = RAGConfig.TOP_K_RESULTS
    ):
        """
        Initialize document retriever.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory with data
            top_k: Number of results to return
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.top_k = top_k

        # Initialize vector DB
        if USE_CHROMADB:
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = PersistentClient(
                path=str(persist_directory)
            )

        # Get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            raise ValueError(
                f"Collection '{collection_name}' not found. "
                f"Please run indexing first. Error: {e}"
            )

        # Initialize embedder
        self.embedder = EmbeddingGenerator()

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results (overrides default)
            filter_metadata: Optional metadata filters

        Returns:
            List of results with document text, metadata, and score
        """
        k = top_k or self.top_k

        # Generate query embedding
        query_embedding = self.embedder.generate_query_embedding(query)

        # Search in vector DB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_metadata
        )

        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                result = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'id': results['ids'][0][i]
                }
                formatted_results.append(result)

        return formatted_results

    def search_by_file(self, query: str, file_name: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Search within a specific file.

        Args:
            query: Search query
            file_name: File name to search in
            top_k: Number of results

        Returns:
            List of results from the specified file
        """
        filter_metadata = {"file_name": file_name}
        return self.search(query, top_k, filter_metadata)

    def get_context_for_query(self, query: str, max_length: int = 2000) -> str:
        """
        Get concatenated context for a query, suitable for LLM prompt.

        Args:
            query: Search query
            max_length: Maximum character length of context

        Returns:
            Formatted context string
        """
        results = self.search(query)

        if not results:
            return "No relevant documentation found."

        # Build context
        context_parts = []
        total_length = 0

        for i, result in enumerate(results):
            source = result['metadata'].get('source', 'Unknown')
            text = result['text']

            part = f"[Source {i+1}: {source}]\n{text}\n"
            part_length = len(part)

            if total_length + part_length > max_length:
                break

            context_parts.append(part)
            total_length += part_length

        return "\n".join(context_parts)

    def get_related_files(self, query: str, limit: int = 5) -> List[str]:
        """
        Get list of files related to a query.

        Args:
            query: Search query
            limit: Maximum number of files

        Returns:
            List of unique file paths
        """
        results = self.search(query, top_k=limit * 2)

        # Extract unique file sources
        files = []
        seen = set()

        for result in results:
            source = result['metadata'].get('source')
            if source and source not in seen:
                files.append(source)
                seen.add(source)

            if len(files) >= limit:
                break

        return files
