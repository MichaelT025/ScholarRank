"""ScholarRank TUI Application entry point."""

from dotenv import load_dotenv
from textual.app import App

from src.storage.database import init_db
from src.tui.screens import ChatScreen


class ScholarRankApp(App):
    """Main TUI application for ScholarRank."""

    TITLE = "ScholarRank"
    CSS_PATH = "tui/app.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        # Initialize database on startup
        init_db()

    def on_mount(self) -> None:
        """Push the chat screen when app mounts."""
        self.push_screen(ChatScreen())


def main() -> None:
    """Entry point for the application."""
    load_dotenv()
    app = ScholarRankApp()
    app.run()


if __name__ == "__main__":
    main()
