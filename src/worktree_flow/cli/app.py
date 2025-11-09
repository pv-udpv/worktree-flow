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
    no_envrc: bool = typer.Option(
        False,
        "--no-envrc",
        help="Skip .envrc creation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing .envrc",
    ),
):
    """Initialize repository for worktree workflow.

    Creates .envrc configuration file with example settings.
    If direnv is installed, the environment will be automatically loaded.

    Example:
        worktree init
        worktree init /path/to/repo
        worktree init --no-envrc
        worktree init --force
    """
    from ..core.init import initialize_repository
    
    console.print(f"[bold]Initializing worktree workflow for:[/bold] {repo_path}")
    console.print()
    
    # Initialize repository
    results = initialize_repository(
        repo_path=repo_path,
        create_envrc=not no_envrc,
        force_create=force,
    )
    
    # Display results
    if results["envrc_created"]:
        console.print("[green]✓[/green] Created .envrc configuration file")
        console.print(f"  → {repo_path / '.envrc'}")
    elif results["envrc_exists"]:
        if results["envrc_valid"]:
            console.print("[green]✓[/green] Found existing .envrc file")
        else:
            console.print("[yellow]⚠[/yellow] Found .envrc but validation failed")
        console.print(f"  → {repo_path / '.envrc'}")
    
    # Check direnv
    if results["direnv_available"]:
        console.print("[green]✓[/green] direnv is available")
        if results["envrc_exists"]:
            console.print("  → Run [bold]direnv allow[/bold] to load environment")
    else:
        console.print("[yellow]⚠[/yellow] direnv is not installed")
        console.print("  → Install direnv to automatically load .envrc")
        console.print("  → Visit: https://direnv.net/")
    
    # Show loaded environment variables
    if results["loaded_env_vars"]:
        console.print()
        console.print("[bold]Environment variables found in .envrc:[/bold]")
        for key, value in sorted(results["loaded_env_vars"].items()):
            # Truncate long values
            display_value = value if len(value) <= 50 else value[:47] + "..."
            console.print(f"  • {key} = {display_value}")
    
    console.print()
    console.print("[green]✓[/green] Initialization complete!")
    console.print()
    console.print("[dim]Next steps:[/dim]")
    console.print("  1. Edit .envrc to configure your environment")
    if results["direnv_available"]:
        console.print("  2. Run [bold]direnv allow[/bold] to load the environment")
        console.print("  3. Start using worktree commands")
    else:
        console.print("  2. Source .envrc manually or install direnv")
        console.print("  3. Start using worktree commands")


@app.command()
def create(
    issue_id: str = typer.Argument(..., help="Issue ID or number"),
    provider: str = typer.Option(
        settings.default_issue_provider,
        "--provider",
        "-p",
        help="Provider name (github, linear, jira)",
    ),
    repo_path: Path = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path",
    ),
):
    """Create worktree from issue.

    Examples:
        worktree create 7
        worktree create DEV-123 --provider linear
        worktree create 7 --repo /path/to/repo
    """
    console.print(f"[bold]Creating worktree from issue {issue_id}[/bold]")
    console.print(f"Provider: {provider}")
    if repo_path:
        console.print(f"Repository: {repo_path}")
    console.print("[yellow]⚠️  Not implemented yet - coming soon![/yellow]")


@app.command()
def epic(
    issue_id: str = typer.Argument(..., help="Epic issue ID"),
    repo_path: Path = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path",
    ),
):
    """Create epic-level worktree.

    Examples:
        worktree epic 7
        worktree epic 7 --repo /path/to/repo
    """
    console.print(f"[bold]Creating epic worktree from issue {issue_id}[/bold]")
    if repo_path:
        console.print(f"Repository: {repo_path}")
    console.print("[yellow]⚠️  Not implemented yet - coming soon![/yellow]")


@app.command()
def feature(
    issue_id: str = typer.Argument(..., help="Feature issue ID"),
    parent: str = typer.Argument(..., help="Parent worktree name"),
    repo_path: Path = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path",
    ),
):
    """Create feature worktree under epic.

    Examples:
        worktree feature 7.1 epic-7
        worktree feature 7.1 epic-7 --repo /path/to/repo
    """
    console.print(f"[bold]Creating feature worktree from issue {issue_id}[/bold]")
    console.print(f"Parent: {parent}")
    if repo_path:
        console.print(f"Repository: {repo_path}")
    console.print("[yellow]⚠️  Not implemented yet - coming soon![/yellow]")


@app.command()
def list(
    repo_path: Path = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path",
    ),
):
    """List all worktrees.

    Examples:
        worktree list
        worktree list --repo /path/to/repo
    """
    console.print("[bold]Listing worktrees...[/bold]")
    if repo_path:
        console.print(f"Repository: {repo_path}")
    console.print("[yellow]⚠️  Not implemented yet - coming soon![/yellow]")


@app.command()
def info(
    worktree_name: str = typer.Argument(..., help="Worktree name"),
    repo_path: Path = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository path",
    ),
):
    """Show worktree information.

    Examples:
        worktree info issue-7
        worktree info epic-7 --repo /path/to/repo
    """
    console.print(f"[bold]Worktree info: {worktree_name}[/bold]")
    if repo_path:
        console.print(f"Repository: {repo_path}")
    console.print("[yellow]⚠️  Not implemented yet - coming soon![/yellow]")


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
