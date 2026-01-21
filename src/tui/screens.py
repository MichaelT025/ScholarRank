"""TUI screens for ScholarRank."""

import asyncio
import os
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog, Static

from src.config import load_profile, save_profile, profile_exists
from src.profile.models import UserProfile
from src.tui.commands import CommandParser, CommandResult, CommandType


class InterviewScreen(Screen):
    """Screen for conducting the profile interview."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    InterviewScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto auto;
    }

    #interview-header {
        dock: top;
        height: 3;
        background: $secondary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #interview-container {
        height: 1fr;
        border: solid $secondary;
        padding: 1 2;
    }

    #interview-log {
        height: 100%;
        scrollbar-gutter: stable;
    }

    #interview-input-container {
        height: auto;
        padding: 1 2;
    }

    #interview-input {
        dock: bottom;
    }

    #interview-status {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.interviewer: Optional["ProfileInterviewer"] = None
        self.profile: Optional[UserProfile] = None
        self._interview_started = False

    def compose(self) -> ComposeResult:
        """Compose the interview screen layout."""
        yield Static(
            "[bold]Profile Interview[/bold]",
            id="interview-header",
        )

        with Vertical(id="interview-container"):
            yield RichLog(id="interview-log", highlight=True, markup=True)

        with Container(id="interview-input-container"):
            yield Input(
                placeholder="Type your response...",
                id="interview-input",
            )

        yield Static(
            "[dim]Type your response and press Enter | Escape to cancel[/dim]",
            id="interview-status",
        )

    async def on_mount(self) -> None:
        """Handle screen mount - start the interview."""
        output = self.query_one("#interview-log", RichLog)
        self.query_one("#interview-input", Input).focus()

        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            output.write("[red]Error: OPENAI_API_KEY environment variable not set.[/red]")
            output.write("")
            output.write("Please set your OpenAI API key:")
            output.write("  [cyan]export OPENAI_API_KEY='your-key-here'[/cyan]")
            output.write("")
            output.write("Press [bold]Escape[/bold] to go back.")
            return

        # Initialize interviewer
        try:
            from src.profile.interview import ProfileInterviewer
            self.interviewer = ProfileInterviewer()
        except Exception as e:
            output.write(f"[red]Error initializing interviewer: {e}[/red]")
            output.write("Press [bold]Escape[/bold] to go back.")
            return

        # Check for existing profile
        if profile_exists():
            existing = load_profile()
            if not existing.is_empty():
                output.write("[yellow]You already have a profile.[/yellow]")
                output.write(f"Completion: {existing.completion_percentage():.0f}%")
                output.write("")
                output.write("Starting interview will update your existing profile.")
                output.write("")

        # Show initial message
        initial = self.interviewer.get_initial_message()
        output.write(f"[bold cyan]Assistant:[/bold cyan] {initial}")
        output.write("")
        self._interview_started = True

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user response."""
        if not self._interview_started or not self.interviewer:
            return

        user_input = event.value.strip()
        if not user_input:
            return

        # Clear input
        event.input.value = ""

        output = self.query_one("#interview-log", RichLog)
        output.write(f"[bold green]You:[/bold green] {user_input}")
        output.write("")

        # Show thinking indicator
        output.write("[dim]Thinking...[/dim]")

        try:
            # Process response
            response, profile = await self.interviewer.process_response(user_input)

            # Remove thinking indicator (write new content)
            # Clean the response for display
            display_response = response
            if "[PROFILE_COMPLETE]" in display_response:
                # Don't show the JSON in the chat
                display_response = display_response.split("[PROFILE_COMPLETE]")[0].strip()
                if not display_response:
                    display_response = "Great! I've created your profile."

            output.write(f"[bold cyan]Assistant:[/bold cyan] {display_response}")
            output.write("")

            if profile:
                self.profile = profile
                # Save the profile
                save_profile(profile)
                output.write("[bold green]Profile saved successfully![/bold green]")
                output.write("")
                
                # Show summary
                summary = profile.get_summary()
                output.write("[bold]Profile Summary:[/bold]")
                for key, value in summary.items():
                    if value is not None:
                        output.write(f"  {key}: {value}")
                output.write("")
                output.write("Press [bold]Escape[/bold] to return to main screen.")
                self._interview_started = False

        except Exception as e:
            output.write(f"[red]Error: {e}[/red]")
            output.write("Please try again or press Escape to cancel.")

    def action_cancel(self) -> None:
        """Cancel the interview and return to main screen."""
        self.app.pop_screen()


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
        
        # Check for existing profile
        if profile_exists():
            profile = load_profile()
            if not profile.is_empty():
                self.profile_loaded = True
                output.write(f"[green]Profile loaded[/green] ({profile.completion_percentage():.0f}% complete)")
                output.write("")
        
        if not self.profile_loaded:
            output.write("Welcome! Type [bold]/init[/bold] to create your profile,")
            output.write("or [bold]/help[/bold] to see available commands.")
        else:
            output.write("Type [bold]/help[/bold] to see available commands.")
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
                self.app.push_screen(InterviewScreen())
            case CommandType.PROFILE:
                self._show_profile()
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

    def _show_profile(self) -> None:
        """Show current profile."""
        output = self.query_one("#output-log", RichLog)
        
        if not profile_exists():
            output.write("[yellow]No profile found. Run /init to create one.[/yellow]")
            output.write("")
            return
        
        profile = load_profile()
        if profile.is_empty():
            output.write("[yellow]Profile is empty. Run /init to fill it in.[/yellow]")
            output.write("")
            return
        
        output.write("[bold]Your Profile[/bold]")
        output.write(f"Completion: {profile.completion_percentage():.0f}%")
        output.write("")
        
        summary = profile.get_summary()
        for key, value in summary.items():
            if value is not None and key != "completion":
                if isinstance(value, list):
                    value = ", ".join(value) if value else "None"
                output.write(f"  [cyan]{key}:[/cyan] {value}")
        
        output.write("")
        output.write("Run [bold]/init[/bold] to update your profile.")
        output.write("")
