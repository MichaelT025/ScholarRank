from textual.widgets import Static
from textual.app import ComposeResult

class ChatBubble(Static):
    """A styled chat message bubble."""
    
    def __init__(self, message: str, is_user: bool = False, **kwargs):
        super().__init__(message, **kwargs)
        self.is_user = is_user
        self.add_class("user-bubble" if is_user else "assistant-bubble")
