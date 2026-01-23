"""ScholarRank TUI Application entry point."""

import logging

from dotenv import load_dotenv
from textual.app import App

from src.config import FETCH_ERRORS_LOG_PATH, ensure_data_dir
from src.storage.database import init_db
from src.tui.screens import ChatScreen


def configure_logging() -> None:
    """Configure application logging."""
    ensure_data_dir()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    log_path = str(FETCH_ERRORS_LOG_PATH.resolve())
    has_file_handler = any(
        isinstance(handler, logging.FileHandler)
        and handler.baseFilename == log_path
        for handler in root_logger.handlers
    )
    if not has_file_handler:
        file_handler = logging.FileHandler(FETCH_ERRORS_LOG_PATH, encoding="utf-8")
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


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
    configure_logging()
    app = ScholarRankApp()
    app.run()


if __name__ == "__main__":
    main()
