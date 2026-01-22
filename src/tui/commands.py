"""Command parser for slash commands."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable


class CommandType(Enum):
    """Types of slash commands."""

    HELP = auto()
    QUIT = auto()
    INIT = auto()
    RESUME = auto()
    PROFILE = auto()
    FETCH = auto()
    SOURCES = auto()
    MATCH = auto()
    INFO = auto()
    SAVE = auto()
    STATS = auto()
    CLEAN = auto()
    APIKEY = auto()
    UNKNOWN = auto()


@dataclass
class CommandResult:
    """Result of parsing a command."""

    command_type: CommandType
    args: list[str]
    raw_input: str
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        """Check if the command is valid."""
        return self.error is None and self.command_type != CommandType.UNKNOWN


class CommandParser:
    """Parser for slash commands."""

    COMMANDS = {
        "/help": CommandType.HELP,
        "/quit": CommandType.QUIT,
        "/exit": CommandType.QUIT,
        "/q": CommandType.QUIT,
        "/init": CommandType.INIT,
        "/resume": CommandType.RESUME,
        "/profile": CommandType.PROFILE,
        "/fetch": CommandType.FETCH,
        "/sources": CommandType.SOURCES,
        "/match": CommandType.MATCH,
        "/info": CommandType.INFO,
        "/save": CommandType.SAVE,
        "/stats": CommandType.STATS,
        "/clean": CommandType.CLEAN,
        "/apikey": CommandType.APIKEY,
    }

    HELP_TEXT = """
[bold #d4af37]Available Commands:[/bold #d4af37]
  [bold #10b981]/help[/bold #10b981]              Show this help message
  [bold #10b981]/quit[/bold #10b981], /exit, /q   Exit the application
  [bold #10b981]/init[/bold #10b981]              Run LLM interview to create/update profile
  [bold #10b981]/resume[/bold #10b981]            Resume an interrupted interview
  [bold #10b981]/profile[/bold #10b981]           Show current profile
  [bold #10b981]/fetch[/bold #10b981]             Fetch scholarships from all sources
  [bold #10b981]/sources[/bold #10b981]           List available sources and status
  [bold #10b981]/match[/bold #10b981]             Find matching scholarships
  [bold #10b981]/info <id>[/bold #10b981]         Show detailed scholarship info
  [bold #10b981]/save [filename][/bold #10b981]   Save matches to file (JSON, CSV, or MD)
  [bold #10b981]/stats[/bold #10b981]             Show database statistics
  [bold #10b981]/clean[/bold #10b981]             Remove expired scholarships
  [bold #10b981]/apikey <key>[/bold #10b981]      Set OpenAI API key

[bold #d4af37]Keyboard Shortcuts:[/bold #d4af37]
  [bold #a0a0a0]Ctrl+Q[/bold #a0a0a0]             Quit the application
  [bold #a0a0a0]Ctrl+C[/bold #a0a0a0]             Quit the application
  [bold #a0a0a0]Up/Down[/bold #a0a0a0]            Navigate list
  [bold #a0a0a0]Enter[/bold #a0a0a0]              View selected item
  """

    def parse(self, input_text: str) -> CommandResult:
        """Parse a command string.

        Args:
            input_text: The raw input text from the user.

        Returns:
            CommandResult with parsed command and arguments.
        """
        input_text = input_text.strip()

        if not input_text:
            return CommandResult(
                command_type=CommandType.UNKNOWN,
                args=[],
                raw_input=input_text,
                error="Empty command",
            )

        if not input_text.startswith("/"):
            return CommandResult(
                command_type=CommandType.UNKNOWN,
                args=[],
                raw_input=input_text,
                error="Commands must start with /",
            )

        parts = input_text.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if command in self.COMMANDS:
            return CommandResult(
                command_type=self.COMMANDS[command],
                args=args,
                raw_input=input_text,
            )

        return CommandResult(
            command_type=CommandType.UNKNOWN,
            args=args,
            raw_input=input_text,
            error=f"Unknown command: {command}. Type /help for available commands.",
        )

    def get_help_text(self) -> str:
        """Get the help text for all commands."""
        return self.HELP_TEXT.strip()
