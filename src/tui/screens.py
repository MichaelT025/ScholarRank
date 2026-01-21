"""TUI screens for ScholarRank."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog, Static

from src.tui.commands import CommandParser, CommandResult, CommandType


class MainScreen(Screen):
    """Main application screen with command input and output display."""

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "focus_input", "Focus Input"),
    ]

    CSS = """
    MainScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto auto;
    }

    #header-bar {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #profile-status {
        dock: right;
        width: auto;
        padding: 0 2;
    }

    #output-container {
        height: 1fr;
        border: solid $primary;
        padding: 1 2;
    }

    #output-log {
        height: 100%;
        scrollbar-gutter: stable;
    }

    #input-container {
        height: auto;
        padding: 1 2;
    }

    #command-input {
        dock: bottom;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.command_parser = CommandParser()
        self.profile_loaded = False

    def compose(self) -> ComposeResult:
        """Compose the main screen layout."""
        yield Header()

        with Vertical(id="output-container"):
            yield RichLog(id="output-log", highlight=True, markup=True)

        with Container(id="input-container"):
            yield Input(
                placeholder="Type a command (e.g., /help)",
                id="command-input",
            )

        yield Static(
            "[dim]Type /help for commands | Ctrl+Q to quit[/dim]",
            id="status-bar",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount."""
        self.query_one("#command-input", Input).focus()
        output = self.query_one("#output-log", RichLog)
        output.write("[bold cyan]SCHOLARRANK[/bold cyan] v0.1.0")
        output.write("")
        output.write("Welcome! Type [bold]/init[/bold] to create your profile,")
        output.write("or [bold]/help[/bold] to see available commands.")
        output.write("")

    def action_focus_input(self) -> None:
        """Focus the command input."""
        self.query_one("#command-input", Input).focus()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command_text = event.value.strip()
        if not command_text:
            return

        # Clear input
        event.input.value = ""

        # Log the command
        output = self.query_one("#output-log", RichLog)
        output.write(f"[bold green]>[/bold green] {command_text}")

        # Parse and execute
        result = self.command_parser.parse(command_text)
        self._execute_command(result)

    def _execute_command(self, result: CommandResult) -> None:
        """Execute a parsed command."""
        output = self.query_one("#output-log", RichLog)

        if not result.is_valid:
            output.write(f"[red]{result.error}[/red]")
            output.write("")
            return

        match result.command_type:
            case CommandType.HELP:
                self._show_help()
            case CommandType.QUIT:
                self.app.exit()
            case CommandType.INIT:
                output.write("[yellow]Profile interview not yet implemented.[/yellow]")
                output.write("This will be added in Phase 2 (Task 5).")
            case CommandType.PROFILE:
                output.write("[yellow]Profile display not yet implemented.[/yellow]")
                output.write("This will be added in Phase 2 (Task 4).")
            case CommandType.FETCH:
                output.write("[yellow]Fetching not yet implemented.[/yellow]")
                output.write("This will be added in Phase 3 (Tasks 7-12).")
            case CommandType.SOURCES:
                output.write("[yellow]Sources list not yet implemented.[/yellow]")
                output.write("This will be added in Phase 7 (Task 20).")
            case CommandType.MATCH:
                output.write("[yellow]Matching not yet implemented.[/yellow]")
                output.write("This will be added in Phase 6 (Task 17).")
            case CommandType.INFO:
                if result.args:
                    output.write(
                        f"[yellow]Info for scholarship {result.args[0]} not yet implemented.[/yellow]"
                    )
                else:
                    output.write("[red]Usage: /info <id>[/red]")
                output.write("This will be added in Phase 6 (Task 18).")
            case CommandType.SAVE:
                filename = result.args[0] if result.args else "matches.json"
                output.write(f"[yellow]Saving to {filename} not yet implemented.[/yellow]")
                output.write("This will be added in Phase 6 (Task 19).")
            case CommandType.STATS:
                output.write("[yellow]Stats not yet implemented.[/yellow]")
                output.write("This will be added in Phase 7 (Task 20).")
            case CommandType.CLEAN:
                output.write("[yellow]Clean not yet implemented.[/yellow]")
                output.write("This will be added in Phase 7 (Task 20).")
            case _:
                output.write(f"[red]Unhandled command: {result.command_type}[/red]")

        output.write("")

    def _show_help(self) -> None:
        """Show help text."""
        output = self.query_one("#output-log", RichLog)
        help_text = self.command_parser.get_help_text()
        for line in help_text.split("\n"):
            output.write(line)
        output.write("")
