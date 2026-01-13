"""CLI interface for the development assistant."""

import click
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .assistant import DevelopmentAssistant
from ..rag.indexer import DocumentIndexer
from ..rag.config import RAGConfig

console = Console()


@click.group()
def cli():
    """Development Assistant with RAG and MCP."""
    pass


@cli.command()
@click.argument('query', required=False)
def help(query):
    """
    Get help about the project.

    Usage:
        python -m src.assistant.cli help
        python -m src.assistant.cli help "How does authentication work?"
    """
    try:
        assistant = DevelopmentAssistant()

        with console.status("[bold green]Thinking..."):
            response = assistant.help(query)

        # Display response
        console.print("\n")
        console.print(Panel(Markdown(response), title="Assistant", border_style="blue"))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@cli.command()
@click.argument('query')
@click.option('--limit', default=5, help='Number of results')
def search(query, limit):
    """
    Search project documentation.

    Usage:
        python -m src.assistant.cli search "authentication"
    """
    try:
        assistant = DevelopmentAssistant()
        results = assistant.search_docs(query, limit)

        console.print("\n")
        console.print(Markdown(results))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@cli.command()
@click.argument('query')
def files(query):
    """
    Find files related to a query.

    Usage:
        python -m src.assistant.cli files "authentication"
    """
    try:
        assistant = DevelopmentAssistant()
        results = assistant.get_related_files(query)

        console.print("\n")
        console.print(Markdown(results))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@cli.command()
@click.option('--docs-path', default='./docs', help='Path to documentation directory')
@click.option('--clear', is_flag=True, help='Clear existing index first')
def index(docs_path, clear):
    """
    Index project documentation.

    Usage:
        python -m src.assistant.cli index
        python -m src.assistant.cli index --docs-path ./docs --clear
    """
    try:
        console.print("[bold blue]Starting indexing...[/bold blue]")

        indexer = DocumentIndexer()

        if clear:
            console.print("[yellow]Clearing existing index...[/yellow]")
            indexer.clear_collection()

        # Index docs directory
        docs_dir = Path(docs_path)
        if docs_dir.exists():
            console.print(f"[green]Indexing: {docs_dir}[/green]")
            count = indexer.index_directory(docs_dir)
            console.print(f"[bold green]Indexed {count} chunks from docs[/bold green]")
        else:
            console.print(f"[yellow]Warning: {docs_dir} not found[/yellow]")

        # Also index README if exists
        readme = Path('./README.md')
        if readme.exists():
            console.print("[green]Indexing: README.md[/green]")
            with open(readme) as f:
                indexer.index_text(
                    f.read(),
                    metadata={'source': 'README.md', 'file_name': 'README.md'}
                )
            console.print("[bold green]Indexed README.md[/bold green]")

        # Show stats
        stats = indexer.get_stats()
        console.print("\n[bold]Index Statistics:[/bold]")
        console.print(f"  Collection: {stats['collection_name']}")
        console.print(f"  Documents: {stats['document_count']}")
        console.print(f"  Location: {stats['persist_directory']}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@cli.command()
def git():
    """
    Show git repository context.

    Usage:
        python -m src.assistant.cli git
    """
    try:
        from ..mcp.server import MCPServer

        mcp = MCPServer()
        context = mcp.get_context()

        console.print("\n[bold blue]Git Repository Context[/bold blue]\n")

        # Branch
        branch = context.get('branch', {})
        if 'name' in branch:
            console.print(f"[bold]Branch:[/bold] {branch['name']}")
            console.print(f"[bold]Commit:[/bold] {branch.get('commit', 'N/A')[:8]}")
            console.print(f"[bold]Message:[/bold] {branch.get('commit_message', 'N/A')}")
            console.print()

        # Status
        status = context.get('status', {})
        if status and not status.get('error'):
            console.print("[bold]Status:[/bold]")
            console.print(f"  Modified: {len(status.get('modified', []))}")
            console.print(f"  Staged: {len(status.get('staged', []))}")
            console.print(f"  Untracked: {len(status.get('untracked', []))}")
            console.print()

        # Recent commits
        commits = context.get('recent_commits', [])
        if commits and not any('error' in c for c in commits):
            console.print("[bold]Recent Commits:[/bold]")
            for commit in commits:
                console.print(f"  {commit['hash']}: {commit['message']}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@cli.command()
def interactive():
    """
    Start interactive assistant session.

    Usage:
        python -m src.assistant.cli interactive
    """
    try:
        assistant = DevelopmentAssistant()

        console.print(Panel(
            "[bold blue]Development Assistant[/bold blue]\n\n"
            "Type your questions or commands:\n"
            "  - Ask any question about the project\n"
            "  - Type 'quit' or 'exit' to leave\n"
            "  - Type 'git' to see git context",
            border_style="green"
        ))

        while True:
            try:
                query = console.input("\n[bold cyan]You:[/bold cyan] ")

                if query.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if query.lower() == 'git':
                    git_context = assistant.get_git_context()
                    console.print(Markdown(git_context))
                    continue

                if not query.strip():
                    continue

                with console.status("[bold green]Thinking..."):
                    response = assistant.help(query)

                console.print("\n[bold green]Assistant:[/bold green]")
                console.print(Markdown(response))

            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == '__main__':
    cli()
