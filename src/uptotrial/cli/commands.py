"""CLI commands for the UpToTrial application."""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from uptotrial import __version__
from uptotrial.core.config import get_settings

# Create Typer app
app = typer.Typer(
    name="uptotrial",
    help="UpToTrial CLI for clinical trials search",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


@app.command()
def version():
    """Display the current version of the UpToTrial CLI."""
    console.print(f"UpToTrial CLI v{__version__}")


@app.command()
def config():
    """Display the current configuration."""
    settings = get_settings()
    
    # Create a table for the settings
    table = Table(title="UpToTrial Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Add selected settings to the table
    table.add_row("Environment", settings.environment)
    table.add_row("Debug Mode", str(settings.debug))
    table.add_row("Database", settings.database_identifier)
    table.add_row("OpenAI Model", settings.openai_model)
    
    console.print(table)


@app.command()
def search(
    query: str = typer.Argument(..., help="Natural language query for clinical trials"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results to return"),
):
    """Search for clinical trials using natural language.
    
    Args:
        query: Natural language query
        limit: Maximum number of results
    """
    # This is a placeholder - actual implementation will connect to the search service
    console.print(f"Searching for: [bold cyan]{query}[/bold cyan]")
    console.print(f"Limit: {limit}")
    console.print("\n[yellow]This feature is not yet implemented.[/yellow]")
    
    # In the future, this will display a table of search results
    # table = Table(title="Search Results")
    # table.add_column("NCT ID", style="cyan")
    # table.add_column("Title", style="green")
    # table.add_column("Status", style="yellow")
    # console.print(table)


if __name__ == "__main__":
    app()