"""Simple chat-based TUI screen for ScholarRank."""

import asyncio
import logging
import os
from typing import Optional, TYPE_CHECKING

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Static, ProgressBar
from textual.containers import Vertical
from textual.binding import Binding

from src.tui.commands import CommandParser, CommandType
from src.config import load_profile, save_profile, profile_exists, INTERVIEW_DRAFT_PATH
from src.tui.components import ChatLog

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.profile.interview import ProfileInterviewer


class ChatScreen(Screen):
    """Main chat screen - simple input at bottom, messages above."""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("escape", "focus_input", "Focus Input", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.command_parser = CommandParser()
        self.interviewer: Optional["ProfileInterviewer"] = None
        self._in_interview = False

    def compose(self) -> ComposeResult:
        yield Static("ScholarRank", id="header")
        yield ProgressBar(total=100, show_eta=False, id="interview-progress")
        yield ChatLog(id="chat-log")
        with Vertical(id="input-container"):
            yield Input(placeholder="Type a command (/help) or message...", id="input")
            yield Static("Ctrl+Q Quit • /init Start Interview • /help Commands", id="tips")

    async def on_mount(self) -> None:
        """Show welcome message on mount."""
        log = self.query_one("#chat-log", ChatLog)
        log.write("[bold cyan]Welcome to ScholarRank[/bold cyan]")
        log.write("[dim]Type /help for available commands[/dim]")
        log.write("")
        
        # Focus the input
        self.query_one("#input", Input).focus()

    def action_focus_input(self) -> None:
        """Focus the input field."""
        self.query_one("#input", Input).focus()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _write_user_message(self, log: ChatLog, text: str) -> None:
        """Write a user message as a bubble."""
        log.add_bubble(text, is_user=True)

    def _write_ai_message(self, log: ChatLog, text: str) -> None:
        """Write an AI message as a bubble."""
        log.add_bubble(text, is_user=False)

    def _begin_ai_stream(self, log: ChatLog) -> Static:
        """Start an AI streaming response."""
        return log.start_stream(is_user=False)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        text = event.value.strip()
        if not text:
            return

        # Clear input
        event.input.value = ""

        log = self.query_one("#chat-log", ChatLog)

        # Show user input with formatting
        self._write_user_message(log, text)

        # Check if in interview mode
        if self._in_interview and self.interviewer:
            await self._handle_interview_input(text, log)
            return

        # Check if it's a command
        if text.startswith("/"):
            await self._handle_command(text, log)
        else:
            # Not a command and not in interview - show hint
            log.write("")
            log.write("[dim]Type /help for commands or /init to start profile interview[/dim]")
        
        log.write("")

    async def _handle_command(self, text: str, log: ChatLog) -> None:
        """Handle slash commands."""
        result = self.command_parser.parse(text)

        if not result.is_valid:
            log.write(f"[red]{result.error}[/red]")
            return

        match result.command_type:
            case CommandType.HELP:
                await self._cmd_help(log)
            case CommandType.QUIT:
                self.app.exit()
            case CommandType.INIT:
                await self._cmd_init(log, result.args)
            case CommandType.RESUME:
                await self._cmd_resume(log, result.args)
            case CommandType.PROFILE:
                await self._cmd_profile(log)
            case CommandType.FETCH:
                await self._cmd_fetch(log, result.args)
            case CommandType.SOURCES:
                await self._cmd_sources(log)
            case CommandType.MATCH:
                await self._cmd_match(log, result.args)
            case CommandType.INFO:
                await self._cmd_info(log, result.args)
            case CommandType.SAVE:
                await self._cmd_save(log, result.args)
            case CommandType.STATS:
                await self._cmd_stats(log)
            case CommandType.CLEAN:
                await self._cmd_clean(log)
            case CommandType.APIKEY:
                await self._cmd_apikey(log, result.args)
            case _:
                log.write(f"[red]Unknown command. Type /help for available commands.[/red]")

    async def _cmd_help(self, log: ChatLog) -> None:
        """Show help message."""
        log.write(self.command_parser.get_help_text())

    async def _cmd_init(self, log: ChatLog, args: list[str] | None = None) -> None:
        """Start profile interview."""
        if not os.getenv("OPENAI_API_KEY"):
            log.write("[red]OPENAI_API_KEY not set.[/red]")
            log.write("[dim]Use /apikey <key> to set it, or export OPENAI_API_KEY[/dim]")
            return

        # Check for --new flag
        start_new = args and "--new" in args
        if start_new:
            # Start fresh, clear any existing draft
            if INTERVIEW_DRAFT_PATH.exists():
                INTERVIEW_DRAFT_PATH.unlink()
            log.write("[dim]Starting new interview...[/dim]")

        try:
            from src.profile.interview import ProfileInterviewer

            # Check for existing interview draft
            draft_exists = INTERVIEW_DRAFT_PATH.exists()

            if draft_exists and not start_new:
                log.write("[yellow]Found an incomplete interview draft.[/yellow]")
                log.write("[dim]Type /resume to continue or /init --new to start over.[/dim]")
                return

            self.interviewer = ProfileInterviewer(draft_path=str(INTERVIEW_DRAFT_PATH))
            self._in_interview = True

            # Show and reset progress bar
            progress_bar = self.query_one("#interview-progress", ProgressBar)
            progress_bar.add_class("visible")
            progress_bar.update(progress=0)

            if profile_exists():
                existing = load_profile()
                if not existing.is_empty():
                    log.write(f"[yellow]Existing profile found ({existing.completion_percentage():.0f}% complete)[/yellow]")
                    log.write("[dim]Your responses will update the existing profile.[/dim]")

            initial = self.interviewer.get_initial_message()
            self._write_ai_message(log, initial)

        except Exception as e:
            log.write(f"[red]Error starting interview: {e}[/red]")
            self._in_interview = False
            self.interviewer = None

    async def _cmd_resume(self, log: ChatLog, args: list[str] | None = None) -> None:
        """Resume an interrupted interview."""
        if not os.getenv("OPENAI_API_KEY"):
            log.write("[red]OPENAI_API_KEY not set.[/red]")
            log.write("[dim]Use /apikey <key> to set it, or export OPENAI_API_KEY[/dim]")
            return

        try:
            from src.profile.interview import ProfileInterviewer

            # Check for --new flag
            start_new = args and "--new" in args

            if start_new:
                # Start fresh, clear any existing draft
                if INTERVIEW_DRAFT_PATH.exists():
                    INTERVIEW_DRAFT_PATH.unlink()
                log.write("[dim]Starting new interview...[/dim]")
                return await self._cmd_init(log)

            # Check for existing draft
            if not INTERVIEW_DRAFT_PATH.exists():
                log.write("[yellow]No interview draft found. Use /init to start one.[/yellow]")
                return

            # Load from draft
            self.interviewer = ProfileInterviewer(draft_path=str(INTERVIEW_DRAFT_PATH))
            loaded = self.interviewer.load_draft()

            if not loaded:
                log.write("[red]Failed to load interview draft. Use /init --new to start fresh.[/red]")
                return

            self._in_interview = True

            # Show and reset progress bar
            progress_bar = self.query_one("#interview-progress", ProgressBar)
            progress_bar.add_class("visible")
            self._update_interview_progress()

            log.write("[green]Resuming interview...[/green]")
            log.write("[dim]Your conversation history has been restored.[/dim]")
            log.write("")
            log.write("[dim]Continue responding to the last question, or type /cancel to exit.[/dim]")

        except Exception as e:
            log.write(f"[red]Error resuming interview: {e}[/red]")
            self._in_interview = False
            self.interviewer = None

    def _update_interview_progress(self) -> None:
        """Update interview progress bar based on conversation turns."""
        if not self.interviewer:
            return
        # Each turn = 2 messages (user + assistant), max_turns default is 10
        turns = len(self.interviewer.conversation_history) // 2
        max_turns = getattr(self.interviewer, 'max_turns', 10)
        progress = min(100, int((turns / max_turns) * 100))
        try:
            progress_bar = self.query_one("#interview-progress", ProgressBar)
            progress_bar.update(progress=progress)
        except Exception:
            pass

    def _hide_interview_progress(self) -> None:
        """Hide the interview progress bar."""
        try:
            progress_bar = self.query_one("#interview-progress", ProgressBar)
            progress_bar.remove_class("visible")
        except Exception:
            pass

    async def _handle_interview_input(self, text: str, log: ChatLog) -> None:
        """Handle input during interview mode with streaming."""
        if text.lower() in ["/cancel", "/quit", "/exit"]:
            # Try to extract and save partial profile
            if self.interviewer:
                try:
                    partial_profile = await self.interviewer.extract_partial_profile()
                    if partial_profile and not partial_profile.is_empty():
                        save_profile(partial_profile)
                        log.write("")
                        log.write(f"[green]Partial profile saved ({partial_profile.completion_percentage():.0f}% complete)[/green]")
                except Exception as e:
                    logger.warning(f"Failed to save partial profile on cancel: {e}")
                    log.write("")
                    log.write("[yellow]Interview cancelled. Progress has been saved to draft.[/yellow]")
                    return

            self._in_interview = False
            self.interviewer = None
            self._hide_interview_progress()
            log.write("")
            log.write("[yellow]Interview cancelled.[/yellow]")
            return

        if not self.interviewer:
            log.write("[red]Interview not initialized. Run /init again.[/red]")
            self._in_interview = False
            return

        # Start streaming response
        stream_entry = self._begin_ai_stream(log)
        
        try:
            interviewer = self.interviewer
            full_message = ""
            profile = None
            stream_text = ""
            display_enabled = True
            marker = "[PROFILE_COMPLETE]"
            
            async for event_type, content in interviewer.process_response_streaming(text):
                if event_type == "chunk" and isinstance(content, str):
                    full_message += content

                    if not display_enabled:
                        continue

                    marker_index = full_message.find(marker)
                    if marker_index != -1:
                        display_enabled = False
                        # Clean up any partial marker that might have been displayed
                        stream_text = full_message[:marker_index]
                    else:
                        stream_text += content

                    stream_entry.update(stream_text)
                    log.scroll_end(animate=False)
                    # Yield to Textual's event loop to allow UI repaint
                    await asyncio.sleep(0)
                elif event_type == "done":
                    if isinstance(content, tuple):
                        full_message, profile = content

            log.write("")
            
            # Update progress bar after each exchange
            self._update_interview_progress()
            
            if profile:
                save_profile(profile)
                self._in_interview = False
                self.interviewer = None
                self._hide_interview_progress()
                
                # Set progress to 100% before hiding
                try:
                    progress_bar = self.query_one("#interview-progress", ProgressBar)
                    progress_bar.update(progress=100)
                except Exception:
                    pass
                
                log.write("[green]Profile saved successfully![/green]")
                log.write("")
                
                # Show summary
                summary = profile.get_summary()
                log.write("[bold]Profile Summary:[/bold]")
                for key, value in summary.items():
                    if value is not None:
                        log.write(f"      {key}: {value}")
                log.write("")

        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")
            log.write("[dim]Try again or type /cancel to exit interview[/dim]")

    async def _cmd_profile(self, log: ChatLog) -> None:
        """Show current profile."""
        if not profile_exists():
            log.write("[yellow]No profile found. Run /init to create one.[/yellow]")
            return

        profile = load_profile()
        summary = profile.get_summary()
        
        log.write(f"[bold]Profile ({profile.completion_percentage():.0f}% complete)[/bold]")
        for key, value in summary.items():
            if value is not None:
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                log.write(f"  [cyan]{key}:[/cyan] {value}")

    async def _cmd_fetch(self, log: ChatLog, args: list[str]) -> None:
        """Fetch scholarships from sources."""
        log.write("[yellow]Fetching scholarships... (this may take a while)[/yellow]")
        
        try:
            from src.scrapers import (
                FastwebScraper,
                ScholarshipsComScraper,
                CareerOneStopScraper,
                IEFAScraper,
                Scholars4devScraper,
            )
            from src.storage.database import get_session
            from src.storage.models import Scholarship, FetchLog
            from sqlalchemy import func
            from datetime import datetime
            
            # Get count before
            session = next(get_session())
            before_count = session.query(func.count(Scholarship.id)).scalar() or 0
            
            scrapers = [
                ("Fastweb", FastwebScraper),
                ("Scholarships.com", ScholarshipsComScraper),
                ("CareerOneStop", CareerOneStopScraper),
                ("IEFA", IEFAScraper),
                ("Scholars4dev", Scholars4devScraper),
            ]
            
            results = {}
            for name, scraper_class in scrapers:
                log.write(f"[dim]  Fetching {name}...[/dim]")
                try:
                    scraper = scraper_class()
                    scholarships = await scraper.scrape()
                    count = len(scholarships) if scholarships else 0
                    results[name] = {"count": count}
                    
                    # Log fetch
                    fetch_log = FetchLog(
                        source=name.lower().replace(".", "_").replace(" ", "_"),
                        fetched_at=datetime.now(),
                        scholarships_found=count,
                    )
                    session.add(fetch_log)
                    session.commit()
                    
                except Exception as e:
                    results[name] = {"error": str(e)}
                    log.write(f"  [red]{name}: {e}[/red]")
            
            # Get count after
            session = next(get_session())
            after_count = session.query(func.count(Scholarship.id)).scalar() or 0
            new_count = after_count - before_count
            
            log.write(f"[green]Fetch complete![/green]")
            log.write(f"  Total scholarships: {after_count}")
            log.write(f"  New this run: {new_count}")
            
            # Show per-source results
            for source, result in results.items():
                if result.get("error"):
                    log.write(f"  [red]{source}: Error - {result['error']}[/red]")
                else:
                    log.write(f"  [dim]{source}: {result.get('count', 0)} scholarships[/dim]")
                    
        except Exception as e:
            log.write(f"[red]Fetch failed: {e}[/red]")

    async def _cmd_sources(self, log: ChatLog) -> None:
        """List available sources and their status."""
        from src.storage.database import get_session
        from src.storage.models import FetchLog
        
        sources = [
            ("Fastweb", "fastweb"),
            ("Scholarships.com", "scholarships_com"),
            ("CareerOneStop", "careeronestop"),
            ("IEFA", "iefa"),
            ("Scholars4dev", "scholars4dev"),
        ]
        
        log.write("[bold]Scholarship Sources[/bold]")
        
        session = next(get_session())
        for name, key in sources:
            last_fetch = (
                session.query(FetchLog)
                .filter_by(source=key)
                .order_by(FetchLog.fetched_at.desc())
                .first()
            )
            
            if last_fetch:
                if last_fetch.errors:
                    status = f"[red]Error: {last_fetch.errors[:30]}...[/red]"
                else:
                    status = f"[green]{last_fetch.fetched_at.strftime('%Y-%m-%d %H:%M')}[/green] ({last_fetch.scholarships_found} found)"
            else:
                status = "[dim]Never fetched[/dim]"
            
            log.write(f"  {name}: {status}")

    async def _cmd_match(self, log: ChatLog, args: list[str]) -> None:
        """Find matching scholarships."""
        if not profile_exists():
            log.write("[yellow]No profile found. Run /init first.[/yellow]")
            return

        log.write("[yellow]Running matcher...[/yellow]")

        try:
            from src.storage.database import get_session
            from src.storage.models import Scholarship
            from src.matching.matcher import EligibilityMatcher
            from src.matching.scorer import FitScorer

            profile = load_profile()
            session = next(get_session())
            
            # Load scholarships
            db_scholarships = session.query(Scholarship).all()
            if not db_scholarships:
                log.write("[yellow]No scholarships in database. Run /fetch first.[/yellow]")
                return

            scholarships_data = []
            for s in db_scholarships:
                scholarships_data.append({
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
                })

            # Match
            matcher = EligibilityMatcher()
            match_results = matcher.match_batch(profile, scholarships_data)
            
            # Score
            scorer = FitScorer()
            fit_scores = scorer.score_batch(match_results, scholarships_data)
            
            # Combine and sort
            for i, (s, match_res, fit) in enumerate(zip(scholarships_data, match_results, fit_scores)):
                s["match_result"] = match_res.to_dict()
                s["fit_score"] = fit.total

            # Filter eligible and sort by score
            eligible = [s for s in scholarships_data if s["match_result"]["eligible"]]
            eligible.sort(key=lambda x: x["fit_score"], reverse=True)
            
            # Parse limit from args
            limit = 10
            for arg in args:
                if arg.startswith("--limit="):
                    try:
                        limit = int(arg.split("=")[1])
                    except ValueError:
                        pass
                elif arg.isdigit():
                    limit = int(arg)

            log.write(f"[green]Found {len(eligible)} eligible matches out of {len(scholarships_data)} total[/green]")
            log.write("")
            
            # Display top matches
            for i, s in enumerate(eligible[:limit], 1):
                score_pct = int(s["fit_score"] * 100)
                if score_pct >= 80:
                    score_style = "green"
                elif score_pct >= 60:
                    score_style = "yellow"
                else:
                    score_style = "red"
                
                amount = self._format_amount(s.get("amount_min"), s.get("amount_max"))
                deadline = s.get("deadline", "Open")[:10] if s.get("deadline") else "Open"
                
                log.write(f"[bold]{i}. {s['title'][:50]}[/bold]")
                log.write(f"   [{score_style}]{score_pct}% fit[/{score_style}] | {amount} | Deadline: {deadline}")
                log.write(f"   [dim]{s.get('source', 'Unknown')}[/dim]")
            
            if len(eligible) > limit:
                log.write(f"[dim]...and {len(eligible) - limit} more. Use /match --limit=N to see more.[/dim]")

        except Exception as e:
            log.write(f"[red]Matching failed: {e}[/red]")

    def _format_amount(self, amount_min: Optional[int], amount_max: Optional[int]) -> str:
        """Format amount for display."""
        if amount_max:
            dollars = amount_max // 100
            if dollars >= 10000:
                return f"${dollars // 1000}k"
            return f"${dollars:,}"
        elif amount_min:
            dollars = amount_min // 100
            return f"${dollars:,}+"
        return "Varies"

    async def _cmd_info(self, log: ChatLog, args: list[str]) -> None:
        """Show detailed info for a scholarship."""
        if not args:
            log.write("[yellow]Usage: /info <scholarship_id>[/yellow]")
            return

        scholarship_id = args[0]
        
        try:
            from src.storage.database import get_session
            from src.storage.models import Scholarship
            
            session = next(get_session())
            scholarship = session.query(Scholarship).filter_by(id=scholarship_id).first()
            
            if not scholarship:
                log.write(f"[red]Scholarship not found: {scholarship_id}[/red]")
                return

            log.write(f"[bold]{scholarship.title}[/bold]")
            log.write(f"[dim]Source: {scholarship.source}[/dim]")
            log.write("")
            
            amount = self._format_amount(scholarship.amount_min, scholarship.amount_max)
            log.write(f"[cyan]Amount:[/cyan] {amount}")
            
            if scholarship.deadline:
                log.write(f"[cyan]Deadline:[/cyan] {scholarship.deadline.strftime('%Y-%m-%d')}")
            else:
                log.write("[cyan]Deadline:[/cyan] Open/Rolling")
            
            if scholarship.description:
                log.write("")
                log.write("[cyan]Description:[/cyan]")
                # Truncate long descriptions
                desc = scholarship.description[:500]
                for line in desc.split("\n"):
                    log.write(f"  {line}")
                if len(scholarship.description) > 500:
                    log.write("  ...")
            
            if scholarship.application_url:
                log.write("")
                log.write(f"[cyan]Apply:[/cyan] {scholarship.application_url}")

        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    async def _cmd_save(self, log: ChatLog, args: list[str]) -> None:
        """Save matches to file."""
        if not profile_exists():
            log.write("[yellow]No profile found. Run /init and /match first.[/yellow]")
            return

        filename = args[0] if args else "matches.json"
        
        # Determine format from extension
        if filename.endswith(".csv"):
            fmt = "csv"
        elif filename.endswith(".md"):
            fmt = "markdown"
        else:
            fmt = "json"

        log.write(f"[yellow]Saving matches to {filename}...[/yellow]")

        try:
            from src.storage.database import get_session
            from src.storage.models import Scholarship
            from src.matching.matcher import EligibilityMatcher
            from src.matching.scorer import FitScorer
            import json
            import csv

            profile = load_profile()
            session = next(get_session())
            db_scholarships = session.query(Scholarship).all()

            if not db_scholarships:
                log.write("[yellow]No scholarships to save. Run /fetch first.[/yellow]")
                return

            # Run matching
            scholarships_data = []
            for s in db_scholarships:
                scholarships_data.append({
                    "id": s.id,
                    "title": s.title,
                    "source": s.source,
                    "amount_min": s.amount_min,
                    "amount_max": s.amount_max,
                    "deadline": s.deadline.isoformat() if s.deadline else None,
                    "application_url": s.application_url,
                })

            matcher = EligibilityMatcher()
            match_results = matcher.match_batch(profile, scholarships_data)
            
            scorer = FitScorer()
            fit_scores = scorer.score_batch(match_results, scholarships_data)

            for i, (s, match_res, fit) in enumerate(zip(scholarships_data, match_results, fit_scores)):
                s["eligible"] = match_res.eligible
                s["fit_score"] = fit.total

            # Filter and sort
            eligible = [s for s in scholarships_data if s["eligible"]]
            eligible.sort(key=lambda x: x["fit_score"], reverse=True)

            # Save based on format
            if fmt == "json":
                with open(filename, "w") as f:
                    json.dump(eligible, f, indent=2, default=str)
            elif fmt == "csv":
                with open(filename, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["title", "source", "fit_score", "deadline", "application_url"])
                    writer.writeheader()
                    for s in eligible:
                        writer.writerow({
                            "title": s["title"],
                            "source": s["source"],
                            "fit_score": f"{int(s['fit_score'] * 100)}%",
                            "deadline": s["deadline"] or "Open",
                            "application_url": s["application_url"] or "",
                        })
            elif fmt == "markdown":
                with open(filename, "w") as f:
                    f.write("# Scholarship Matches\n\n")
                    for i, s in enumerate(eligible, 1):
                        f.write(f"## {i}. {s['title']}\n\n")
                        f.write(f"- **Fit Score:** {int(s['fit_score'] * 100)}%\n")
                        f.write(f"- **Source:** {s['source']}\n")
                        f.write(f"- **Deadline:** {s['deadline'] or 'Open'}\n")
                        if s["application_url"]:
                            f.write(f"- **Apply:** {s['application_url']}\n")
                        f.write("\n")

            log.write(f"[green]Saved {len(eligible)} matches to {filename}[/green]")

        except Exception as e:
            log.write(f"[red]Save failed: {e}[/red]")

    async def _cmd_stats(self, log: ChatLog) -> None:
        """Show database statistics."""
        try:
            from src.storage.database import get_session
            from src.storage.models import Scholarship, FetchLog
            from sqlalchemy import func
            from datetime import datetime, timedelta

            session = next(get_session())
            
            total = session.query(func.count(Scholarship.id)).scalar() or 0
            
            # Count by source
            by_source = (
                session.query(Scholarship.source, func.count(Scholarship.id))
                .group_by(Scholarship.source)
                .all()
            )
            
            # Recent (last 24h)
            yesterday = datetime.now() - timedelta(days=1)
            recent_fetches = (
                session.query(FetchLog)
                .filter(FetchLog.fetched_at > yesterday)
                .count()
            )

            log.write("[bold]Database Statistics[/bold]")
            log.write(f"  Total scholarships: {total}")
            log.write(f"  Fetches (24h): {recent_fetches}")
            log.write("")
            log.write("[bold]By Source:[/bold]")
            for source, count in by_source:
                log.write(f"  {source}: {count}")

        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    async def _cmd_clean(self, log: ChatLog) -> None:
        """Remove expired scholarships."""
        try:
            from src.storage.database import get_session
            from src.storage.models import Scholarship
            from datetime import date

            session = next(get_session())
            
            today = date.today()
            expired = session.query(Scholarship).filter(Scholarship.deadline < today).all()
            count = len(expired)
            
            if count == 0:
                log.write("[green]No expired scholarships to remove.[/green]")
                return

            for s in expired:
                session.delete(s)
            session.commit()
            
            log.write(f"[green]Removed {count} expired scholarships.[/green]")

        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    async def _cmd_apikey(self, log: ChatLog, args: list[str]) -> None:
        """Set OpenAI API key."""
        if not args:
            current = os.getenv("OPENAI_API_KEY")
            if current:
                masked = current[:8] + "..." + current[-4:]
                log.write(f"[green]API key is set: {masked}[/green]")
            else:
                log.write("[yellow]No API key set. Use /apikey <key> to set one.[/yellow]")
            return

        key = args[0]
        os.environ["OPENAI_API_KEY"] = key
        
        # Also try to save to .env file
        try:
            env_path = ".env"
            lines = []
            key_found = False
            
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            lines.append(f"OPENAI_API_KEY={key}\n")
                            key_found = True
                        else:
                            lines.append(line)
            
            if not key_found:
                lines.append(f"OPENAI_API_KEY={key}\n")
            
            with open(env_path, "w") as f:
                f.writelines(lines)
            
            log.write("[green]API key set and saved to .env[/green]")
        except Exception:
            log.write("[green]API key set for this session.[/green]")
            log.write("[dim]Could not save to .env file[/dim]")
