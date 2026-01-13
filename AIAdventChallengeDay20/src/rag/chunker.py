"""Document chunking utilities."""

from typing import List, Dict
from pathlib import Path
from .config import RAGConfig


class DocumentChunker:
    """Split documents into chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = RAGConfig.CHUNK_SIZE,
        chunk_overlap: int = RAGConfig.CHUNK_OVERLAP
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Simple word-based chunking (for production, use proper tokenizer)
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)

            chunk_data = {
                'text': chunk_text,
                'metadata': metadata or {},
                'chunk_index': len(chunks),
            }
            chunks.append(chunk_data)

            if i + self.chunk_size >= len(words):
                break

        return chunks

    def chunk_file(self, file_path: Path) -> List[Dict]:
        """
        Read and chunk a file.

        Args:
            file_path: Path to file

        Returns:
            List of chunks with metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {
                'source': str(file_path),
                'file_name': file_path.name,
                'file_type': file_path.suffix,
            }

            return self.chunk_text(content, metadata)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []

    def chunk_directory(self, directory: Path, extensions: List[str] = None) -> List[Dict]:
        """
        Chunk all files in a directory.

        Args:
            directory: Directory path
            extensions: File extensions to include (e.g., ['.md', '.py'])

        Returns:
            List of all chunks from all files
        """
        if extensions is None:
            extensions = ['.md', '.txt', '.py', '.js', '.json']

        all_chunks = []

        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                chunks = self.chunk_file(file_path)
                all_chunks.extend(chunks)

        return all_chunks
