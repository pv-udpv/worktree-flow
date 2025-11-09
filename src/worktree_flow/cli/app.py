"""Typer CLI application."""

import typer
from rich.console import Console
from pathlib import Path

from ..config import settings

console = Console()
app = typer.Typer(
    name="worktree",
    help="Advanced Git worktree workflow management",
    no_args_is_help=True,
)


@app.command()
def serve(
    host: str = typer.Option(
        settings.api_host,
        "--host",
        "-h",
        help="API host",
    ),
    port: int = typer.Option(
        settings.api_port,
        "--port",
        "-p",
        help="API port",
    ),
    reload: bool = typer.Option(
        settings.api_reload,
        "--reload",
        "-r",
        help="Enable auto-reload",
    ),
):
    """Start FastAPI server.

    Example:
        worktree serve --port 8000 --reload
    """
    console.print("[bold]Starting Worktree Flow API server[/bold]")
    console.print(f"→ http://{host}:{port}")
    console.print(f"→ Docs: http://{host}:{port}/docs")
    console.print(f"→ ReDoc: http://{host}:{port}/redoc")
    console.print()

    from ..api.app import serve as api_serve

    api_serve(host=host, port=port, reload=reload)


@app.command()
def init(
    repo_path: Path = typer.Argument(
        Path.cwd(),
        help="Repository path to initialize",
    ),
):
    """Initialize repository for worktree workflow.

    Example:
        worktree init /path/to/repo
    """
    console.print(f"[bold]Initializing worktree workflow for:[/bold] {repo_path}")
    # TODO: Implement initialization
    console.print("[yellow]⚠️  Not implemented yet - coming soon![/yellow]")


@app.command()
def create(
    issue_id: str = typer.Argument(..., help="Issue ID or number"),
    provider: str = typer.Option(
        settings.default_issue_provider,
        "--provider",
        "-p",
        help="Provider name",
    ),
):
    """Create worktree from issue.

    Example:
        worktree create 7
        worktree create DEV-123 --provider linear
    """
    console.print(f"[bold]Creating worktree from issue {issue_id}[/bold]")
    console.print(f"Provider: {provider}")
    # TODO: Implement with WorktreeManager
    console.print("[yellow]⚠️  Not implemented yet - coming soon![/yellow]")


@app.command()
def list():
    """List all worktrees.

    Example:
        worktree list
    """
    console.print("[bold]Listing worktrees...[/bold]")
    # TODO: Implement listing
    console.print("[yellow]⚠️  Not implemented yet - coming soon![/yellow]")


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
