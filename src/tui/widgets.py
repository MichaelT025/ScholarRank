"""Custom TUI widgets for ScholarRank."""

from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import DataTable, Static


class MatchTable(DataTable):
    """Data table for displaying matched scholarships with fit scores.
    
    8 columns:
    - #: Row number
    - Scholarship: Title (truncated)
    - Amount: Award amount
    - Deadline: Application deadline
    - Fit: Fit score percentage with color
    - Source: Data source
    - Reqs: Requirements met (e.g., "4/5")
    - Status: Eligibility status
    """
    
    BINDINGS = [
        Binding("enter", "select_row", "View Details", show=True),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]
    
    # Column widths
    COLUMNS = [
        ("#", 4),
        ("Scholarship", 35),
        ("Amount", 12),
        ("Deadline", 12),
        ("Fit", 6),
        ("Source", 15),
        ("Reqs", 8),
        ("Status", 10),
    ]
    
    class RowSelected(Message):
        """Message sent when a row is selected."""
        def __init__(self, scholarship_id: str, row_index: int) -> None:
            self.scholarship_id = scholarship_id
            self.row_index = row_index
            super().__init__()
    
    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, cursor_type="row", zebra_stripes=True, **kwargs)
        self._scholarships: List[Dict[str, Any]] = []
        self._id_to_row: Dict[str, int] = {}
    
    def on_mount(self) -> None:
        """Set up table columns on mount."""
        for name, width in self.COLUMNS:
            self.add_column(name, width=width)
    
    def load_scholarships(
        self,
        scholarships: List[Dict[str, Any]],
    ) -> int:
        """Load scholarships into the table.
        
        Args:
            scholarships: List of scholarship dicts with match_result and fit_score
            
        Returns:
            Number of rows added
        """
        self.clear()
        self._scholarships = scholarships
        self._id_to_row = {}
        
        for idx, scholarship in enumerate(scholarships, 1):
            row_key = self._add_scholarship_row(scholarship, idx)
            self._id_to_row[scholarship.get("id", str(idx))] = idx - 1
        
        return len(scholarships)
    
    def _add_scholarship_row(
        self,
        scholarship: Dict[str, Any],
        row_num: int,
    ) -> str:
        """Add a single scholarship row to the table.
        
        Returns:
            Row key
        """
        # Extract data
        title = scholarship.get("title", "Unknown")
        amount_min = scholarship.get("amount_min")
        amount_max = scholarship.get("amount_max")
        deadline = scholarship.get("deadline")
        source = scholarship.get("source", "Unknown")
        fit_score = scholarship.get("fit_score", 0)
        match_result = scholarship.get("match_result", {})
        
        # Format cells
        num_cell = str(row_num)
        title_cell = self._truncate(title, 33)
        amount_cell = self._format_amount(amount_min, amount_max)
        deadline_cell = self._format_deadline(deadline)
        fit_cell = self._format_fit_score(fit_score)
        source_cell = self._truncate(source, 13)
        reqs_cell = self._format_reqs(match_result)
        status_cell = self._format_status(match_result)
        
        row_key = self.add_row(
            num_cell,
            title_cell,
            amount_cell,
            deadline_cell,
            fit_cell,
            source_cell,
            reqs_cell,
            status_cell,
            key=scholarship.get("id", str(row_num)),
        )
        
        return row_key
    
    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis if too long."""
        if len(text) <= max_len:
            return text
        return text[:max_len - 1] + "\u2026"  # ellipsis
    
    def _format_amount(
        self,
        amount_min: Optional[int],
        amount_max: Optional[int],
    ) -> str:
        """Format amount in dollars."""
        if amount_max is None and amount_min is None:
            return "Varies"
        
        # Amounts are stored in cents
        if amount_max:
            dollars = amount_max // 100
            if dollars >= 10000:
                return f"${dollars // 1000}k"
            return f"${dollars:,}"
        elif amount_min:
            dollars = amount_min // 100
            if dollars >= 10000:
                return f"${dollars // 1000}k+"
            return f"${dollars:,}+"
        
        return "Varies"
    
    def _format_deadline(self, deadline: Any) -> Text:
        """Format deadline date with urgency icons."""
        if deadline is None:
            return Text("Open", style="dim")
        
        if isinstance(deadline, str):
            try:
                deadline = date.fromisoformat(deadline)
            except ValueError:
                return Text(deadline[:10], style="dim")
        
        if isinstance(deadline, datetime):
            deadline = deadline.date()
        
        if isinstance(deadline, date):
            today = date.today()
            days_until = (deadline - today).days
            
            if days_until < 0:
                return Text("⚠ Expired", style="red dim")
            elif days_until == 0:
                return Text("🔴 TODAY!", style="bold red")
            elif days_until <= 7:
                return Text(f"⚠ {days_until}d left", style="bold yellow")
            elif days_until <= 30:
                return Text(deadline.strftime("%b %d"), style="yellow")
            else:
                return Text(deadline.strftime("%b %d"), style="green")
        
        return Text(str(deadline)[:10], style="dim")
    
    def _format_fit_score(self, fit_score: float) -> Text:
        """Format fit score with color coding.
        
        - Green (>= 80%): High match
        - Yellow (60-79%): Medium match
        - Red (< 60%): Low match
        """
        percentage = int(fit_score * 100)
        text = f"{percentage}%"
        
        if percentage >= 80:
            style = "bold green"
        elif percentage >= 60:
            style = "bold yellow"
        else:
            style = "bold red"
        
        return Text(text, style=style)
    
    def _format_reqs(self, match_result: Dict[str, Any]) -> str:
        """Format requirements matched."""
        match_count = match_result.get("match_count", 0)
        total = match_result.get("total_requirements", 0)
        partial = match_result.get("partial_count", 0)
        
        if total == 0:
            return "-"
        
        result = f"{match_count}/{total}"
        if partial > 0:
            result += " ~"
        
        return result
    
    def _format_status(self, match_result: Dict[str, Any]) -> Text:
        """Format eligibility status with color and icons."""
        eligible = match_result.get("eligible", True)
        
        if eligible:
            return Text("✓ Eligible", style="bold green")
        else:
            return Text("✗ Ineligible", style="red dim")
    
    def get_selected_scholarship(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected scholarship."""
        if self.cursor_row is None or self.cursor_row >= len(self._scholarships):
            return None
        return self._scholarships[self.cursor_row]
    
    def get_scholarship_by_id(self, scholarship_id: str) -> Optional[Dict[str, Any]]:
        """Get scholarship by ID."""
        for scholarship in self._scholarships:
            if scholarship.get("id") == scholarship_id:
                return scholarship
        return None
    
    def action_select_row(self) -> None:
        """Handle row selection (Enter key)."""
        scholarship = self.get_selected_scholarship()
        if scholarship:
            self.post_message(
                self.RowSelected(
                    scholarship_id=scholarship.get("id", ""),
                    row_index=self.cursor_row or 0,
                )
            )


class MatchSummaryBar(Static):
    """Status bar showing match summary."""
    
    DEFAULT_CSS = """
    MatchSummaryBar {
        height: 1;
        background: $surface;
        padding: 0 2;
    }
    """
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._total = 0
        self._eligible = 0
        self._showing = 0
    
    def update_stats(
        self,
        total: int,
        eligible: int,
        showing: int,
    ) -> None:
        """Update the summary statistics."""
        self._total = total
        self._eligible = eligible
        self._showing = showing
        self._refresh_display()
    
    def _refresh_display(self) -> None:
        """Refresh the display text."""
        parts = []
        
        if self._showing > 0:
            parts.append(f"[bold]{self._showing}[/bold] shown")
        
        if self._eligible != self._showing:
            parts.append(f"[green]{self._eligible}[/green] eligible")
        
        parts.append(f"{self._total} total")
        
        text = " | ".join(parts)
        text += "  [dim]Press Enter to view details, /save to export[/dim]"
        
        self.update(text)


class MatchContainer(Vertical):
    """Container for the match table and summary."""
    
    DEFAULT_CSS = """
    MatchContainer {
        height: 100%;
    }
    
    MatchContainer > MatchTable {
        height: 1fr;
    }
    
    MatchContainer > MatchSummaryBar {
        dock: bottom;
    }
    """
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._table: Optional[MatchTable] = None
        self._summary: Optional[MatchSummaryBar] = None
    
    def compose(self) -> ComposeResult:
        """Compose the container."""
        self._table = MatchTable(id="match-table")
        self._summary = MatchSummaryBar(id="match-summary")
        
        yield self._table
        yield self._summary
    
    def load_matches(
        self,
        scholarships: List[Dict[str, Any]],
        eligible_only: bool = False,
    ) -> int:
        """Load matched scholarships into the container.
        
        Args:
            scholarships: List of scholarships with match results
            eligible_only: Only show eligible scholarships
            
        Returns:
            Number of scholarships shown
        """
        if self._table is None or self._summary is None:
            return 0
        
        # Filter if requested
        if eligible_only:
            filtered = [
                s for s in scholarships
                if s.get("match_result", {}).get("eligible", True)
            ]
        else:
            filtered = scholarships
        
        # Sort by fit score (descending)
        filtered.sort(key=lambda x: x.get("fit_score", 0), reverse=True)
        
        # Load into table
        count = self._table.load_scholarships(filtered)
        
        # Update summary
        total = len(scholarships)
        eligible = sum(
            1 for s in scholarships
            if s.get("match_result", {}).get("eligible", True)
        )
        self._summary.update_stats(total, eligible, count)
        
        return count
    
    @property
    def table(self) -> Optional[MatchTable]:
        """Get the match table widget."""
        return self._table
    
    def get_selected_scholarship(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected scholarship."""
        if self._table:
            return self._table.get_selected_scholarship()
        return None
