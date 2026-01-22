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
Available Commands:
  /help              Show this help message
  /quit, /exit, /q   Exit the application
  /init              Run LLM interview to create/update profile
  /resume            Resume an interrupted interview
  /profile           Show current profile
  /fetch             Fetch scholarships from all sources
  /sources           List available sources and status
  /match             Find matching scholarships
  /info <id>         Show detailed scholarship info
  /save [filename]   Save matches to file (JSON, CSV, or MD)
  /stats             Show database statistics
  /clean             Remove expired scholarships
  /apikey <key>      Set OpenAI API key

Keyboard Shortcuts:
  Ctrl+Q             Quit the application
  Ctrl+C             Quit the application
  Up/Down            Navigate list
  Enter              View selected item
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
