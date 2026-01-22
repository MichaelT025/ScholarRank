"""Minimal TUI components for ScholarRank."""

from typing import Optional
from textual.containers import VerticalScroll
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel


class ChatBubble(Static):
    """A styled chat message bubble."""
    
    def __init__(self, message: str, is_user: bool = False, **kwargs):
        super().__init__(message, **kwargs)
        self.is_user = is_user
        self.add_class("user-bubble" if is_user else "assistant-bubble")


class FetchProgress(Static):
    """Premium loading indicator for scholarship fetching."""
    
    SOURCES = ["Fastweb", "Scholarships.com", "CareerOneStop", "IEFA", "Scholars4dev"]
    SPINNER = ["◇", "◈", "◆", "◈"]
    STATUS_MESSAGES = [
        "Connecting to scholarship databases...",
        "Scanning available opportunities...",
        "Retrieving scholarship details...",
        "Processing eligibility data...",
        "Finalizing results...",
    ]
    
    current_source: reactive[int] = reactive(-1)
    spinner_frame: reactive[int] = reactive(0)
    source_results: reactive[dict] = reactive({})
    is_complete: reactive[bool] = reactive(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._timer = None
    
    def on_mount(self) -> None:
        self._timer = self.set_interval(0.15, self._advance_spinner)
    
    def _advance_spinner(self) -> None:
        if not self.is_complete:
            self.spinner_frame = (self.spinner_frame + 1) % len(self.SPINNER)
    
    def render(self) -> Panel:
        if self.is_complete:
            return self._render_complete()
        return self._render_progress()
    
    def _render_progress(self) -> Panel:
        # Build source list
        lines = []
        for i, source in enumerate(self.SOURCES):
            if i in self.source_results:
                result = self.source_results[i]
                if "error" in result:
                    mark = Text("✗ ", style="bold #ef4444")
                    name = Text(f"{source}", style="#ef4444")
                else:
                    mark = Text("✓ ", style="bold #10b981")
                    name = Text(f"{source}", style="#10b981")
                    count = Text(f" ({result.get('count', 0)})", style="dim #717682")
                    lines.append(Text.assemble("  ", mark, name, count))
                    continue
            elif i == self.current_source:
                mark = Text(f"{self.SPINNER[self.spinner_frame]} ", style="bold #d4af37")
                name = Text(f"{source}", style="bold #d4af37")
            else:
                mark = Text("○ ", style="dim #404040")
                name = Text(f"{source}", style="dim #505050")
            lines.append(Text.assemble("  ", mark, name))
        
        # Status message
        status_idx = max(0, min(self.current_source, len(self.STATUS_MESSAGES) - 1))
        status = self.STATUS_MESSAGES[status_idx] if self.current_source >= 0 else "Preparing..."
        
        header = Text.assemble(
            ("  ", ""),
            (self.SPINNER[self.spinner_frame], "bold #d4af37"),
            ("  ", ""),
            (status, "italic #717682"),
        )
        
        # Progress bar
        progress = (self.current_source + 1) / len(self.SOURCES) if self.current_source >= 0 else 0
        bar_width = 30
        filled = int(bar_width * progress)
        bar = Text.assemble(
            ("  ", ""),
            ("━" * filled, "#d4af37"),
            ("─" * (bar_width - filled), "#303030"),
            (f"  {int(progress * 100):>3}%", "#717682"),
        )
        
        content = Text.assemble(
            header, "\n\n",
            *[Text.assemble(line, "\n") for line in lines],
            "\n", bar,
        )
        
        return Panel(
            content,
            title="[bold #d4af37]Fetching Scholarships[/]",
            title_align="left",
            border_style="#303030",
            padding=(1, 2),
        )
    
    def _render_complete(self) -> Panel:
        total = sum(r.get("count", 0) for r in self.source_results.values() if "error" not in r)
        errors = sum(1 for r in self.source_results.values() if "error" in r)
        
        lines = []
        for i, source in enumerate(self.SOURCES):
            if i in self.source_results:
                result = self.source_results[i]
                if "error" in result:
                    mark = Text("✗ ", style="bold #ef4444")
                    name = Text(f"{source}", style="#ef4444 dim")
                    info = Text(" failed", style="dim #ef4444")
                else:
                    mark = Text("✓ ", style="bold #10b981")
                    name = Text(f"{source}", style="#a0a0a0")
                    info = Text(f" ({result.get('count', 0)})", style="dim #717682")
                lines.append(Text.assemble("  ", mark, name, info))
        
        header = Text.assemble(
            ("  ✓  ", "bold #10b981"),
            (f"Found {total} scholarships", "#e4e5e7"),
        )
        
        if errors > 0:
            header = Text.assemble(header, ("  ", ""), (f"({errors} source{'s' if errors > 1 else ''} failed)", "dim #ef4444"))
        
        content = Text.assemble(
            header, "\n\n",
            *[Text.assemble(line, "\n") for line in lines],
        )
        
        return Panel(
            content,
            title="[bold #10b981]Fetch Complete[/]",
            title_align="left",
            border_style="#10b981",
            padding=(1, 2),
        )
    
    def start_source(self, index: int) -> None:
        """Mark a source as in-progress."""
        self.current_source = index
        self.mutate_reactive(FetchProgress.source_results)
    
    def complete_source(self, index: int, count: int) -> None:
        """Mark a source as complete with count."""
        results = dict(self.source_results)
        results[index] = {"count": count}
        self.source_results = results
    
    def fail_source(self, index: int, error: str) -> None:
        """Mark a source as failed."""
        results = dict(self.source_results)
        results[index] = {"error": error}
        self.source_results = results
    
    def finish(self) -> None:
        """Mark fetch as complete."""
        self.is_complete = True
        if self._timer:
            self._timer.stop()


class ChatLog(VerticalScroll):
    """Scrollable chat log with helper write methods."""

    def write(self, text: str) -> None:
        """Append a generic message (system/log)."""
        widget = Static(text, markup=True, classes="message")
        self.mount(widget)
        self.call_after_refresh(widget.scroll_visible)

    def add_bubble(self, text: str, is_user: bool) -> None:
        """Add a chat bubble."""
        bubble = ChatBubble(text, is_user=is_user)
        self.mount(bubble)
        self.call_after_refresh(bubble.scroll_visible)

    def start_stream(self, is_user: bool = False) -> ChatBubble:
        """Create a streaming bubble and return it."""
        bubble = ChatBubble("", is_user=is_user)
        self.mount(bubble)
        self.call_after_refresh(bubble.scroll_visible)
        return bubble


class CommandSuggestionList(OptionList):
    """Floating command suggestion list."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We need to set classes on init to match CSS
        self.add_class("command-list")
    
    def update_commands(self, filter_text: str, commands: list[str]) -> None:
        """Update the list based on filter text."""
        self.clear_options()
        
        filtered = [cmd for cmd in commands if cmd.startswith(filter_text)]
        
        if not filtered:
            self.remove_class("visible")
            return
            
        for cmd in filtered:
            self.add_option(Option(Text(cmd)))
            
        self.add_class("visible")
        self.highlighted = 0
