from typing import Any, Dict

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, RichLog, Static

class DetailModal(ModalScreen):
    """Modal screen for displaying scholarship details."""
    
    BINDINGS = [("escape", "close", "Close")]
    
    CSS = """
    DetailModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }
    
    #detail-dialog {
        width: 80%;
        height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto;
    }
    
    #modal-header {
        text-style: bold;
        content-align: center middle;
        background: $secondary;
        color: $text;
        padding: 1;
        margin-bottom: 1;
    }

    #detail-content {
        height: 100%;
        scrollbar-gutter: stable;
        border: solid $primary-muted; 
    }
    
    #close-btn {
        dock: bottom;
        width: 100%;
        margin-top: 1;
    }
    """
    
    def __init__(self, scholarship: Dict[str, Any]) -> None:
        super().__init__()
        self._scholarship = scholarship
        
    def compose(self) -> ComposeResult:
        title = self._scholarship.get("title", "Unknown")
        
        with Vertical(id="detail-dialog"):
            yield Static(title, id="modal-header")
            yield RichLog(id="detail-content", highlight=True, markup=True)
            yield Button("Close", id="close-btn", variant="primary")
            
    def on_mount(self) -> None:
        """Display scholarship details."""
        output = self.query_one("#detail-content", RichLog)
        self._render_details(output)
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.dismiss()
            
    def action_close(self) -> None:
        self.dismiss()

    def _render_details(self, output: RichLog) -> None:
        """Render scholarship details to the log."""
        s = self._scholarship
        
        # We already have the title in the header, so maybe just show source
        output.write(f"[dim]Source: {s.get('source', 'Unknown')}[/dim]")
        output.write("")
        
        # Amount
        amount_min = s.get("amount_min")
        amount_max = s.get("amount_max")
        if amount_max:
            output.write(f"[green]Amount:[/green] ${amount_max // 100:,}")
        elif amount_min:
            output.write(f"[green]Amount:[/green] ${amount_min // 100:,}+")
        else:
            output.write("[green]Amount:[/green] Varies")
        
        # Deadline
        deadline = s.get("deadline")
        if deadline:
            output.write(f"[yellow]Deadline:[/yellow] {deadline}")
        else:
            output.write("[yellow]Deadline:[/yellow] Open/Rolling")
        
        # Fit score with breakdown
        fit_score = s.get("fit_score", 0)
        fit_pct = int(fit_score * 100)
        if fit_pct >= 80:
            fit_style = "bold green"
        elif fit_pct >= 60:
            fit_style = "bold yellow"
        else:
            fit_style = "bold red"
        output.write(f"[{fit_style}]Fit Score: {fit_pct}%[/{fit_style}]")
        
        # Show fit score breakdown if available
        fit_breakdown = s.get("fit_score_breakdown", {})
        if fit_breakdown:
            breakdown = fit_breakdown.get("breakdown", {})
            if breakdown:
                output.write("[dim]Breakdown:[/dim]")
                
                # Criteria match (35% weight)
                criteria = breakdown.get("criteria_match", 0)
                criteria_pct = int(criteria * 100)
                output.write(f"  [cyan]Criteria Match:[/cyan] {criteria_pct}%")
                
                # Deadline urgency (20% weight)
                deadline_urg = breakdown.get("deadline_urgency", 0)
                deadline_pct = int(deadline_urg * 100)
                output.write(f"  [cyan]Deadline Urgency:[/cyan] {deadline_pct}%")
                
                # Value density (25% weight)
                value = breakdown.get("value_density", 0)
                value_pct = int(value * 100)
                output.write(f"  [cyan]Value Density:[/cyan] {value_pct}%")
                
                # Competition factor (20% weight)
                competition = breakdown.get("competition_factor", 0)
                competition_pct = int(competition * 100)
                output.write(f"  [cyan]Competition Factor:[/cyan] {competition_pct}%")
        
        output.write("")
        
        # Description
        description = s.get("description")
        if description:
            output.write("[bold]Description[/bold]")
            # Wrap long descriptions
            for line in description[:500].split("\n"):
                output.write(f"  {line}")
            if len(description) > 500:
                output.write("  ...")
            output.write("")
        
        # Requirements matching with enhanced display
        match_result = s.get("match_result", {})
        if match_result:
            output.write("[bold]Requirements[/bold]")
            eligible = match_result.get("eligible", True)
            match_count = match_result.get("match_count", 0)
            total = match_result.get("total_requirements", 0)
            
            status = "[green]Eligible[/green]" if eligible else "[red]Ineligible[/red]"
            output.write(f"  Status: {status}")
            output.write(f"  Matched: {match_count}/{total}")
            output.write("")
            
            details = match_result.get("details", [])
            for detail in details:
                req = detail.get("requirement", "")
                req_status = detail.get("status", "unknown")
                user_val = detail.get("user_value", "")
                required_val = detail.get("required_value", "")
                
                # Select icon based on status
                if req_status == "matched":
                    icon = "[green]\u2713[/green]"
                elif req_status == "partial":
                    icon = "[yellow]~[/yellow]"
                elif req_status == "unmatched":
                    icon = "[red]\u2717[/red]"
                else:
                    icon = "[dim]?[/dim]"
                
                output.write(f"  {icon} {req}")
                
                # Show user value vs required value
                if user_val and user_val != "Not specified":
                    output.write(f"      [dim]Your value:[/dim] {user_val}")
                if required_val and required_val != user_val:
                    output.write(f"      [dim]Required:[/dim] {required_val}")
            output.write("")
        
        # Application link
        url = s.get("application_url")
        if url:
            output.write("[bold]Apply[/bold]")
            output.write(f"  [link={url}]{url}[/link]")
            output.write("")
