"""Development Assistant with RAG and MCP."""

from typing import Dict, Optional
from pathlib import Path
import anthropic

from ..rag.config import RAGConfig
from ..rag.retriever import DocumentRetriever
from ..mcp.server import MCPServer


class DevelopmentAssistant:
    """AI Assistant for development help."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        repo_path: Optional[Path] = None
    ):
        """
        Initialize development assistant.

        Args:
            api_key: Anthropic API key
            repo_path: Path to git repository
        """
        self.api_key = api_key or RAGConfig.ANTHROPIC_API_KEY
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Initialize RAG retriever
        try:
            self.retriever = DocumentRetriever()
        except ValueError as e:
            print(f"Warning: RAG not initialized: {e}")
            self.retriever = None

        # Initialize MCP server
        self.mcp_server = MCPServer(repo_path)

        # System prompt
        self.system_prompt = """You are a helpful development assistant with access to:
1. Project documentation via RAG (Retrieval-Augmented Generation)
2. Git repository context via MCP (Model Context Protocol)

Your role is to help developers by:
- Answering questions about the project
- Providing code examples from documentation
- Explaining API endpoints and database schemas
- Suggesting code style based on project guidelines
- Providing git context (current branch, recent commits, etc.)

Always cite sources when using documentation and provide specific file references."""

    def get_git_context(self) -> str:
        """
        Get current git context as formatted string.

        Returns:
            Formatted git context
        """
        context = self.mcp_server.get_context()

        # Format context
        parts = []

        # Branch info
        branch_info = context.get('branch', {})
        if 'name' in branch_info:
            parts.append(f"**Current Branch:** {branch_info['name']}")

        # Status
        status = context.get('status', {})
        if status and not status.get('error'):
            modified = len(status.get('modified', []))
            staged = len(status.get('staged', []))
            untracked = len(status.get('untracked', []))
            parts.append(f"**Status:** {modified} modified, {staged} staged, {untracked} untracked")

        # Recent commits
        commits = context.get('recent_commits', [])
        if commits and not any('error' in c for c in commits):
            parts.append("\n**Recent Commits:**")
            for commit in commits[:3]:
                parts.append(f"- {commit['hash']}: {commit['message']}")

        return "\n".join(parts) if parts else "No git context available"

    def help(self, query: Optional[str] = None) -> str:
        """
        Answer a help query about the project.

        Args:
            query: Question about the project (if None, returns general help)

        Returns:
            Assistant's response
        """
        if not query:
            return self._general_help()

        # Get RAG context
        rag_context = ""
        if self.retriever:
            rag_context = self.retriever.get_context_for_query(query)

        # Get git context
        git_context = self.get_git_context()

        # Build prompt
        user_message = f"""Question: {query}

**Git Context:**
{git_context}

**Relevant Documentation:**
{rag_context}

Please answer the question based on the provided context. If you reference documentation, mention the source file."""

        # Call Claude
        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        return response.content[0].text

    def _general_help(self) -> str:
        """
        Provide general help information.

        Returns:
            General help text
        """
        git_context = self.get_git_context()

        help_text = f"""# Development Assistant

I can help you with:
- Understanding project architecture and code
- API endpoints and database schemas
- Code style guidelines
- Git history and context

## Current Repository Status

{git_context}

## Example Questions

- "How does authentication work in this project?"
- "What API endpoints are available?"
- "Show me an example of error handling"
- "What's the database schema for users?"
- "What coding style should I follow?"

Ask me anything about the project!"""

        return help_text

    def search_docs(self, query: str, limit: int = 5) -> str:
        """
        Search documentation and return formatted results.

        Args:
            query: Search query
            limit: Number of results

        Returns:
            Formatted search results
        """
        if not self.retriever:
            return "RAG not initialized. Please run indexing first."

        results = self.retriever.search(query, top_k=limit)

        if not results:
            return "No results found."

        output = [f"# Search Results for: {query}\n"]

        for i, result in enumerate(results):
            source = result['metadata'].get('source', 'Unknown')
            text = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']

            output.append(f"## Result {i+1}")
            output.append(f"**Source:** {source}")
            output.append(f"**Content:** {text}")
            output.append("")

        return "\n".join(output)

    def get_related_files(self, query: str) -> str:
        """
        Get files related to a query.

        Args:
            query: Search query

        Returns:
            List of related files
        """
        if not self.retriever:
            return "RAG not initialized."

        files = self.retriever.get_related_files(query)

        if not files:
            return "No related files found."

        output = [f"# Files related to: {query}\n"]
        for i, file in enumerate(files):
            output.append(f"{i+1}. {file}")

        return "\n".join(output)
