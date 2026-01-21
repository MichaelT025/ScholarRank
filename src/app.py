"""ScholarRank TUI Application entry point."""

from textual.app import App

from src.storage.database import init_db
from src.tui.screens import MainScreen


class ScholarRankApp(App):
    """Main TUI application for ScholarRank."""

    TITLE = "ScholarRank"
    SUB_TITLE = "Scholarship Matching Tool"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        # Initialize database on startup
        init_db()

    def on_mount(self) -> None:
        """Push the main screen when app mounts."""
        self.push_screen(MainScreen())


def main() -> None:
    """Entry point for the application."""
    app = ScholarRankApp()
    app.run()


if __name__ == "__main__":
    main()
