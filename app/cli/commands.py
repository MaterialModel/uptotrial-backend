"""CLI commands for the UpToTrial application."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from app import __version__
from app.config import get_settings
from app.services.clinical_trials_agent.clinical_trials_agent import conversation

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
    
    console.print(table)


@app.command()
def chat() -> None:
    """Start an interactive chat with the Clinical Trials Agent."""
    console.print("[bold green]Starting Clinical Trials Agent chat...[/bold green]")
    console.print("[dim](Type 'exit' to quit the conversation)[/dim]")
    console.print("-" * 50)
    
    async def run_chat() -> None:
        # Initialize the conversation
        conv = conversation()
        # Start the generator - this first next() call just initializes the generator
        await conv.__anext__()
        
        try:
            while True:
                user_input = console.input("[bold cyan]You:[/bold cyan] ")
                if user_input.lower() == "exit":
                    await conv.aclose()
                    break
                
                with console.status("[bold yellow]Agent is thinking...[/bold yellow]"):
                    response = await conv.asend(user_input)
                
                console.print(f"[bold green]Agent:[/bold green] {response}")
                
        except KeyboardInterrupt:
            console.print("\n[bold red]Exiting chat...[/bold red]")
        except StopAsyncIteration:
            console.print("\n[bold red]Conversation ended.[/bold red]")
        finally:
            # Clean up by closing the generator
            await conv.aclose()
    
    # Run the async function
    asyncio.run(run_chat())


if __name__ == "__main__":
    app()