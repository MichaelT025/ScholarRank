"""Minimal TUI components for ScholarRank."""

from textual.containers import VerticalScroll
from textual.widgets import Static


class ChatBubble(Static):
    """A styled chat message bubble."""
    
    def __init__(self, message: str, is_user: bool = False, **kwargs):
        super().__init__(message, **kwargs)
        self.is_user = is_user
        self.add_class("user-bubble" if is_user else "assistant-bubble")


class ChatLog(VerticalScroll):
    """Scrollable chat log with helper write methods."""

    def write(self, text: str) -> None:
        """Append a generic message (system/log)."""
        self.mount(Static(text, markup=True, classes="message"))
        self.scroll_end(animate=False)

    def add_bubble(self, text: str, is_user: bool) -> None:
        """Add a chat bubble."""
        self.mount(ChatBubble(text, is_user=is_user))
        self.scroll_end(animate=False)

    def start_stream(self, is_user: bool = False) -> ChatBubble:
        """Create a streaming bubble and return it."""
        bubble = ChatBubble("", is_user=is_user)
        self.mount(bubble)
        self.scroll_end(animate=False)
        return bubble
