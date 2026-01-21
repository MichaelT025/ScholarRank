"""TUI screens for ScholarRank."""

import asyncio
import os
from typing import Any, Dict, List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog, Static

from src.config import load_profile, save_profile, profile_exists
from src.profile.models import UserProfile
from src.tui.commands import CommandParser, CommandResult, CommandType
from src.tui.widgets import MatchContainer, MatchTable
from src.output import export_scholarships


class InterviewScreen(Screen):
    """Screen for conducting the profile interview."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    InterviewScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto auto;
    }

    #interview-header {
        dock: top;
        height: 3;
        background: $secondary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #interview-container {
        height: 1fr;
        border: solid $secondary;
        padding: 1 2;
    }

    #interview-log {
        height: 100%;
        scrollbar-gutter: stable;
    }

    #interview-input-container {
        height: auto;
        padding: 1 2;
    }

    #interview-input {
        dock: bottom;
    }

    #interview-status {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.interviewer: Optional["ProfileInterviewer"] = None
        self.profile: Optional[UserProfile] = None
        self._interview_started = False

    def compose(self) -> ComposeResult:
        """Compose the interview screen layout."""
        yield Static(
            "[bold]Profile Interview[/bold]",
            id="interview-header",
        )

        with Vertical(id="interview-container"):
            yield RichLog(id="interview-log", highlight=True, markup=True)

        with Container(id="interview-input-container"):
            yield Input(
                placeholder="Type your response...",
                id="interview-input",
            )

        yield Static(
            "[dim]Type your response and press Enter | Escape to cancel[/dim]",
            id="interview-status",
        )

    async def on_mount(self) -> None:
        """Handle screen mount - start the interview."""
        output = self.query_one("#interview-log", RichLog)
        self.query_one("#interview-input", Input).focus()

        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            output.write("[red]Error: OPENAI_API_KEY environment variable not set.[/red]")
            output.write("")
            output.write("Please set your OpenAI API key:")
            output.write("  [cyan]export OPENAI_API_KEY='your-key-here'[/cyan]")
            output.write("")
            output.write("Press [bold]Escape[/bold] to go back.")
            return

        # Initialize interviewer
        try:
            from src.profile.interview import ProfileInterviewer
            self.interviewer = ProfileInterviewer()
        except Exception as e:
            output.write(f"[red]Error initializing interviewer: {e}[/red]")
            output.write("Press [bold]Escape[/bold] to go back.")
            return

        # Check for existing profile
        if profile_exists():
            existing = load_profile()
            if not existing.is_empty():
                output.write("[yellow]You already have a profile.[/yellow]")
                output.write(f"Completion: {existing.completion_percentage():.0f}%")
                output.write("")
                output.write("Starting interview will update your existing profile.")
                output.write("")

        # Show initial message
        initial = self.interviewer.get_initial_message()
        output.write(f"[bold cyan]Assistant:[/bold cyan] {initial}")
        output.write("")
        self._interview_started = True

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user response."""
        if not self._interview_started or not self.interviewer:
            return

        user_input = event.value.strip()
        if not user_input:
            return

        # Clear input
        event.input.value = ""

        output = self.query_one("#interview-log", RichLog)
        output.write(f"[bold green]You:[/bold green] {user_input}")
        output.write("")

        # Show thinking indicator
        output.write("[dim]Thinking...[/dim]")

        try:
            # Process response
            response, profile = await self.interviewer.process_response(user_input)

            # Remove thinking indicator (write new content)
            # Clean the response for display
            display_response = response
            if "[PROFILE_COMPLETE]" in display_response:
                # Don't show the JSON in the chat
                display_response = display_response.split("[PROFILE_COMPLETE]")[0].strip()
                if not display_response:
                    display_response = "Great! I've created your profile."

            output.write(f"[bold cyan]Assistant:[/bold cyan] {display_response}")
            output.write("")

            if profile:
                self.profile = profile
                # Save the profile
                save_profile(profile)
                output.write("[bold green]Profile saved successfully![/bold green]")
                output.write("")
                
                # Show summary
                summary = profile.get_summary()
                output.write("[bold]Profile Summary:[/bold]")
                for key, value in summary.items():
                    if value is not None:
                        output.write(f"  {key}: {value}")
                output.write("")
                output.write("Press [bold]Escape[/bold] to return to main screen.")
                self._interview_started = False

        except Exception as e:
            output.write(f"[red]Error: {e}[/red]")
            output.write("Please try again or press Escape to cancel.")

    def action_cancel(self) -> None:
        """Cancel the interview and return to main screen."""
        self.app.pop_screen()


class MatchScreen(Screen):
    """Screen for displaying matched scholarships."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "back", "Back"),
    ]

    CSS = """
    MatchScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto;
    }

    #match-header {
        dock: top;
        height: 3;
        background: $secondary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #match-container {
        height: 1fr;
        padding: 1 2;
    }

    #match-footer {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
    }
    """

    def __init__(
        self,
        scholarships: List[Dict[str, Any]],
        eligible_only: bool = False,
    ) -> None:
        super().__init__()
        self._scholarships = scholarships
        self._eligible_only = eligible_only
        self._match_container: Optional[MatchContainer] = None

    def compose(self) -> ComposeResult:
        """Compose the match screen layout."""
        yield Static(
            "[bold]Scholarship Matches[/bold]",
            id="match-header",
        )

        self._match_container = MatchContainer(id="match-container")
        yield self._match_container

        yield Static(
            "[dim]Up/Down: Navigate | Enter: View Details | Escape: Back[/dim]",
            id="match-footer",
        )

    def on_mount(self) -> None:
        """Load matches when screen mounts."""
        if self._match_container:
            count = self._match_container.load_matches(
                self._scholarships,
                eligible_only=self._eligible_only,
            )
            # Focus the table for keyboard navigation
            if self._match_container.table:
                self._match_container.table.focus()

    def on_match_table_row_selected(self, event: MatchTable.RowSelected) -> None:
        """Handle row selection - show detail view."""
        scholarship = None
        if self._match_container:
            scholarship = self._match_container.get_selected_scholarship()
        
        if scholarship:
            # Push detail screen
            self.app.push_screen(DetailScreen(scholarship))

    def action_back(self) -> None:
        """Return to main screen."""
        self.app.pop_screen()


class DetailScreen(Screen):
    """Screen for displaying scholarship details."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "back", "Back"),
    ]

    CSS = """
    DetailScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto;
    }

    #detail-header {
        dock: top;
        height: 3;
        background: $secondary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #detail-container {
        height: 1fr;
        padding: 1 2;
        border: solid $primary;
    }

    #detail-log {
        height: 100%;
        scrollbar-gutter: stable;
    }

    #detail-footer {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
    }
    """

    def __init__(self, scholarship: Dict[str, Any]) -> None:
        super().__init__()
        self._scholarship = scholarship

    def compose(self) -> ComposeResult:
        """Compose the detail screen layout."""
        title = self._scholarship.get("title", "Unknown")
        yield Static(
            f"[bold]{title[:50]}...[/bold]" if len(title) > 50 else f"[bold]{title}[/bold]",
            id="detail-header",
        )

        with Vertical(id="detail-container"):
            yield RichLog(id="detail-log", highlight=True, markup=True)

        yield Static(
            "[dim]Escape: Back[/dim]",
            id="detail-footer",
        )

    def on_mount(self) -> None:
        """Display scholarship details."""
        output = self.query_one("#detail-log", RichLog)
        self._render_details(output)

    def _render_details(self, output: RichLog) -> None:
        """Render scholarship details to the log."""
        s = self._scholarship
        
        # Title and source
        output.write(f"[bold cyan]{s.get('title', 'Unknown')}[/bold cyan]")
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
        
        output.write("[dim]Press Escape to go back[/dim]")

    def action_back(self) -> None:
        """Return to match screen."""
        self.app.pop_screen()


class MainScreen(Screen):
    """Main application screen with command input and output display."""

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "focus_input", "Focus Input"),
    ]

    CSS = """
    MainScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto auto;
    }

    #header-bar {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #profile-status {
        dock: right;
        width: auto;
        padding: 0 2;
    }

    #output-container {
        height: 1fr;
        border: solid $primary;
        padding: 1 2;
    }

    #output-log {
        height: 100%;
        scrollbar-gutter: stable;
    }

    #input-container {
        height: auto;
        padding: 1 2;
    }

    #command-input {
        dock: bottom;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.command_parser = CommandParser()
        self.profile_loaded = False
        self._matched_scholarships: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        """Compose the main screen layout."""
        yield Header()

        with Vertical(id="output-container"):
            yield RichLog(id="output-log", highlight=True, markup=True)

        with Container(id="input-container"):
            yield Input(
                placeholder="Type a command (e.g., /help)",
                id="command-input",
            )

        yield Static(
            "[dim]Type /help for commands | Ctrl+Q to quit[/dim]",
            id="status-bar",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount."""
        self.query_one("#command-input", Input).focus()
        output = self.query_one("#output-log", RichLog)
        output.write("[bold cyan]SCHOLARRANK[/bold cyan] v0.1.0")
        output.write("")
        
        # Check for existing profile
        if profile_exists():
            profile = load_profile()
            if not profile.is_empty():
                self.profile_loaded = True
                output.write(f"[green]Profile loaded[/green] ({profile.completion_percentage():.0f}% complete)")
                output.write("")
        
        if not self.profile_loaded:
            output.write("Welcome! Type [bold]/init[/bold] to create your profile,")
            output.write("or [bold]/help[/bold] to see available commands.")
        else:
            output.write("Type [bold]/help[/bold] to see available commands.")
        output.write("")

    def action_focus_input(self) -> None:
        """Focus the command input."""
        self.query_one("#command-input", Input).focus()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command_text = event.value.strip()
        if not command_text:
            return

        # Clear input
        event.input.value = ""

        # Log the command
        output = self.query_one("#output-log", RichLog)
        output.write(f"[bold green]>[/bold green] {command_text}")

        # Parse and execute
        result = self.command_parser.parse(command_text)
        self._execute_command(result)

    def _execute_command(self, result: CommandResult) -> None:
        """Execute a parsed command."""
        output = self.query_one("#output-log", RichLog)

        if not result.is_valid:
            output.write(f"[red]{result.error}[/red]")
            output.write("")
            return

        match result.command_type:
            case CommandType.HELP:
                self._show_help()
            case CommandType.QUIT:
                self.app.exit()
            case CommandType.INIT:
                self.app.push_screen(InterviewScreen())
            case CommandType.PROFILE:
                self._show_profile()
            case CommandType.FETCH:
                output.write("[yellow]Fetching not yet implemented.[/yellow]")
                output.write("This will be added in Phase 3 (Tasks 7-12).")
            case CommandType.SOURCES:
                output.write("[yellow]Sources list not yet implemented.[/yellow]")
                output.write("This will be added in Phase 7 (Task 20).")
            case CommandType.MATCH:
                self._run_match()
            case CommandType.INFO:
                if result.args:
                    self._show_info(result.args[0])
                else:
                    output.write("[red]Usage: /info <id> or /info <row_number>[/red]")
            case CommandType.SAVE:
                filename = result.args[0] if result.args else "matches.json"
                self._save_matches(filename)
            case CommandType.STATS:
                output.write("[yellow]Stats not yet implemented.[/yellow]")
                output.write("This will be added in Phase 7 (Task 20).")
            case CommandType.CLEAN:
                output.write("[yellow]Clean not yet implemented.[/yellow]")
                output.write("This will be added in Phase 7 (Task 20).")
            case _:
                output.write(f"[red]Unhandled command: {result.command_type}[/red]")

        output.write("")

    def _show_help(self) -> None:
        """Show help text."""
        output = self.query_one("#output-log", RichLog)
        help_text = self.command_parser.get_help_text()
        for line in help_text.split("\n"):
            output.write(line)
        output.write("")

    def _show_profile(self) -> None:
        """Show current profile."""
        output = self.query_one("#output-log", RichLog)
        
        if not profile_exists():
            output.write("[yellow]No profile found. Run /init to create one.[/yellow]")
            output.write("")
            return
        
        profile = load_profile()
        if profile.is_empty():
            output.write("[yellow]Profile is empty. Run /init to fill it in.[/yellow]")
            output.write("")
            return
        
        output.write("[bold]Your Profile[/bold]")
        output.write(f"Completion: {profile.completion_percentage():.0f}%")
        output.write("")
        
        summary = profile.get_summary()
        for key, value in summary.items():
            if value is not None and key != "completion":
                if isinstance(value, list):
                    value = ", ".join(value) if value else "None"
                output.write(f"  [cyan]{key}:[/cyan] {value}")
        
        output.write("")
        output.write("Run [bold]/init[/bold] to update your profile.")
        output.write("")

    def _run_match(self) -> None:
        """Run matching and display results."""
        output = self.query_one("#output-log", RichLog)
        
        # Check for profile
        if not profile_exists():
            output.write("[yellow]No profile found. Run /init to create one first.[/yellow]")
            output.write("")
            return
        
        profile = load_profile()
        if profile.is_empty():
            output.write("[yellow]Profile is empty. Run /init to fill it in first.[/yellow]")
            output.write("")
            return
        
        # Load scholarships from database
        try:
            from src.storage.database import get_session
            from src.storage.models import Scholarship
            from src.matching.matcher import EligibilityMatcher
            from src.matching.scorer import FitScorer
            
            output.write("[dim]Loading scholarships from database...[/dim]")
            
            scholarships = []
            for session in get_session():
                db_scholarships = session.query(Scholarship).all()
                for s in db_scholarships:
                    scholarships.append({
                        "id": s.id,
                        "title": s.title,
                        "source": s.source,
                        "description": s.description,
                        "amount_min": s.amount_min,
                        "amount_max": s.amount_max,
                        "deadline": s.deadline.isoformat() if s.deadline else None,
                        "application_url": s.application_url,
                        "raw_eligibility": s.raw_eligibility,
                        "parsed_eligibility": s.parsed_eligibility or {},
                        "effort_score": s.effort_score,
                        "competition_score": s.competition_score,
                    })
            
            if not scholarships:
                output.write("[yellow]No scholarships in database. Run /fetch first.[/yellow]")
                output.write("")
                return
            
            output.write(f"[dim]Found {len(scholarships)} scholarships, matching...[/dim]")
            
            # Run matching
            matcher = EligibilityMatcher()
            match_results = matcher.match_batch(profile, scholarships)
            
            # Calculate fit scores
            scorer = FitScorer()
            fit_scores = scorer.score_batch(match_results, scholarships)
            
            # Combine results
            for i, (scholarship, match_result, fit_score) in enumerate(
                zip(scholarships, match_results, fit_scores)
            ):
                scholarship["match_result"] = match_result.to_dict()
                scholarship["fit_score"] = fit_score.total
                scholarship["fit_score_breakdown"] = fit_score.to_dict()
            
            # Store for export
            self._matched_scholarships = scholarships
            
            # Show match screen
            eligible_count = sum(1 for r in match_results if r.eligible)
            output.write(f"[green]Matched {eligible_count} eligible scholarships![/green]")
            output.write("")
            
            self.app.push_screen(MatchScreen(scholarships))
            
        except Exception as e:
            output.write(f"[red]Error running match: {e}[/red]")
            output.write("")

    def _show_info(self, identifier: str) -> None:
        """Show detailed info for a scholarship.
        
        Args:
            identifier: Either a scholarship ID or row number (1-based)
        """
        output = self.query_one("#output-log", RichLog)
        
        if not self._matched_scholarships:
            output.write("[yellow]No matches available. Run /match first.[/yellow]")
            output.write("")
            return
        
        scholarship = None
        
        # Try to find by row number first
        try:
            row_num = int(identifier)
            if 1 <= row_num <= len(self._matched_scholarships):
                # Sort by fit score (same as in MatchContainer)
                sorted_scholarships = sorted(
                    self._matched_scholarships,
                    key=lambda x: x.get("fit_score", 0),
                    reverse=True,
                )
                scholarship = sorted_scholarships[row_num - 1]
        except ValueError:
            pass
        
        # Try to find by ID
        if scholarship is None:
            for s in self._matched_scholarships:
                if s.get("id") == identifier:
                    scholarship = s
                    break
        
        if scholarship is None:
            output.write(f"[red]Scholarship not found: {identifier}[/red]")
            output.write("Use row number (e.g., /info 1) or scholarship ID")
            output.write("")
            return
        
        # Push detail screen
        self.app.push_screen(DetailScreen(scholarship))
    
    def _save_matches(self, filename: str) -> None:
        """Save matched scholarships to file.
        
        Args:
            filename: Path to save file (extension determines format)
        """
        output = self.query_one("#output-log", RichLog)
        
        if not self._matched_scholarships:
            output.write("[yellow]No matches to save. Run /match first.[/yellow]")
            output.write("")
            return
        
        try:
            export_scholarships(self._matched_scholarships, filename)
            output.write(f"[green]Saved {len(self._matched_scholarships)} scholarships to {filename}[/green]")
            output.write("")
        except ValueError as e:
            output.write(f"[red]Error: {e}[/red]")
            output.write("Supported formats: .json, .csv, .md, .markdown")
            output.write("")
        except IOError as e:
            output.write(f"[red]Error writing file: {e}[/red]")
            output.write("")
        except Exception as e:
            output.write(f"[red]Unexpected error: {e}[/red]")
            output.write("")
