"""CLI commands for the UpToTrial application."""


import typer
from rich.console import Console
from rich.table import Table

from app import __version__
from app.config import get_settings

# Create Typer app
app = typer.Typer(
    name="uptotrial",
    help="UpToTrial CLI for clinical trials search",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


@app.command()
def version() -> None:
    """Display the current version of the UpToTrial CLI."""
    console.print(f"UpToTrial CLI v{__version__}")


@app.command()
def config() -> None:
    """Display the current configuration."""
    settings = get_settings()
    
    # Create a table for the settings
    table = Table(title="UpToTrial Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Add selected settings to the table
    table.add_row("Environment", settings.environment)
    table.add_row("Debug Mode", str(settings.debug))
    table.add_row("Database", settings.get_database_identifier())
    table.add_row("OpenAI Model", settings.openai_model)
    
    console.print(table)

if __name__ == "__main__":
    app()