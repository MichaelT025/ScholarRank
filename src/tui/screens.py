"""Simple chat-based TUI screen for ScholarRank."""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Static, ProgressBar
from textual.containers import Vertical, Container
from textual.binding import Binding
from textual.message import Message
from textual.worker import Worker, WorkerState

from src.tui.commands import CommandParser, CommandType
from src.config import load_profile, save_profile, profile_exists, INTERVIEW_DRAFT_PATH, DEFAULT_MATCHES_PATH, ensure_data_dir
from src.tui.components import ChatLog, FetchProgress, CommandSuggestionList
from textual import events

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk(Message):
    """Message posted when a streaming chunk arrives."""
    text: str


@dataclass  
class StreamComplete(Message):
    """Message posted when streaming is complete."""
    full_message: str
    profile: Optional["UserProfile"] = None


@dataclass
class StreamError(Message):
    """Message posted when streaming encounters an error."""
    error: str


@dataclass
class FetchStartSource(Message):
    """Message posted when starting to fetch from a source."""
    index: int
    name: str


@dataclass
class FetchSourceComplete(Message):
    """Message posted when a source fetch completes."""
    index: int
    name: str
    count: int


@dataclass
class FetchSourceError(Message):
    """Message posted when a source fetch fails."""
    index: int
    name: str
    error: str


@dataclass
class FetchComplete(Message):
    """Message posted when all fetching is complete."""
    total: int
    new_count: int


WELCOME_ART = r"""
   _____      __         __          ____              __
  / ___/_____/ /_  ____/ /___ ______/ __ \____ _____  / /__
  \__ \/ ___/ __ \/ __  / __ `/ ___/ /_/ / __ `/ __ \/ //_/
 ___/ / /__/ / / / /_/ / /_/ / /  / _, _/ /_/ / / / / ,<
/____/\___/_/ /_/\____/\__,_/_/  /_/ |_|\__,_/_/ /_/_/|_|
"""

if TYPE_CHECKING:
    from src.profile.interview import ProfileInterviewer
    from src.profile.models import UserProfile


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
        self._stream_bubble: Optional[Static] = None
        self._stream_text: str = ""
        self._fetch_progress: Optional[FetchProgress] = None

    def compose(self) -> ComposeResult:
        yield Static("S C H O L A R R A N K", id="header")
        yield ProgressBar(total=100, show_eta=False, id="interview-progress")
        yield ChatLog(id="chat-log")
        with Vertical(id="input-container"):
            yield CommandSuggestionList(id="command-list")
            yield Input(placeholder="Type a command (/help) or message...", id="input")
            yield Static("Ctrl+Q Quit • /init Start Interview • /help Commands", id="tips")

    async def on_mount(self) -> None:
        """Show welcome message on mount."""
        log = self.query_one("#chat-log", ChatLog)
        
        # Build the welcome screen components
        steps = """
[bold]Get Started:[/bold]

[gold3]1.[/gold3] Create your profile   [green]/init[/green]
[gold3]2.[/gold3] Fetch scholarships    [green]/fetch[/green]
[gold3]3.[/gold3] Find top matches      [green]/match[/green]
[gold3]4.[/gold3] Export results        [green]/save[/green]
"""
        
        welcome = Container(
            Static(WELCOME_ART, classes="welcome-logo"),
            Static("PREMIUM SCHOLARSHIP INTELLIGENCE", classes="welcome-subtitle"),
            Static(steps, classes="welcome-box"),
            Static("[dim]Type /help for all commands[/dim]", classes="welcome-footer"),
            classes="welcome-container"
        )
        
        await log.mount(welcome)
        
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

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input text changes."""
        text = event.value
        try:
            cmd_list = self.query_one("#command-list", CommandSuggestionList)
            
            if text.startswith("/"):
                # Get commands
                commands = list(self.command_parser.COMMANDS.keys())
                cmd_list.update_commands(text.lower(), commands)
            else:
                cmd_list.remove_class("visible")
        except Exception:
            pass

    async def on_key(self, event: events.Key) -> None:
        """Handle global key events for suggestion navigation."""
        try:
            cmd_list = self.query_one("#command-list", CommandSuggestionList)
            if cmd_list.has_class("visible"):
                if event.key == "up":
                    cmd_list.action_cursor_up()
                    event.stop()
                    event.prevent_default()
                elif event.key == "down":
                    cmd_list.action_cursor_down()
                    event.stop()
                    event.prevent_default()
                elif event.key == "enter" or event.key == "tab":
                    # Select current option
                    if cmd_list.highlighted is not None:
                        opt = cmd_list.get_option_at_index(cmd_list.highlighted)
                        if opt:
                            input_widget = self.query_one("#input", Input)
                            input_widget.value = str(opt.prompt) + " "
                            input_widget.action_end() # Move cursor to end
                            cmd_list.remove_class("visible")
                            event.stop()
                            event.prevent_default()
                elif event.key == "escape":
                    cmd_list.remove_class("visible")
                    event.stop()
                    event.prevent_default()
        except Exception:
            pass

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        try:
            cmd_list = self.query_one("#command-list", CommandSuggestionList)
            if cmd_list.has_class("visible"):
                cmd_list.remove_class("visible")
        except Exception:
            pass

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
            log.write("[dim]Type /help for commands or /init to start profile interview[/dim]")

    async def _handle_command(self, text: str, log: ChatLog) -> None:
        """Handle slash commands."""
        result = self.command_parser.parse(text)

        if not result.is_valid:
            log.write(f"[#ef4444]{result.error}[/#ef4444]")
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
                log.write(f"[#ef4444]Unknown command. Type /help for available commands.[/#ef4444]")

    async def _cmd_help(self, log: ChatLog) -> None:
        """Show help message."""
        log.write(self.command_parser.get_help_text())

    async def _cmd_init(self, log: ChatLog, args: list[str] | None = None) -> None:
        """Start profile interview."""
        if not os.getenv("OPENAI_API_KEY"):
            log.write("[#ef4444]OPENAI_API_KEY not set.[/#ef4444]\n[dim]Use /apikey <key> to set it, or export OPENAI_API_KEY[/dim]")
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
                log.write("[#f59e0b]Found an incomplete interview draft.[/#f59e0b]\n[dim]Type /resume to continue or /init --new to start over.[/dim]")
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
                    log.write(f"[#f59e0b]Existing profile found ({existing.completion_percentage():.0f}% complete)[/#f59e0b]\n[dim]Your responses will update the existing profile.[/dim]")

            initial = self.interviewer.get_initial_message()
            self._write_ai_message(log, initial)

        except Exception as e:
            log.write(f"[#ef4444]Error starting interview: {e}[/#ef4444]")
            self._in_interview = False
            self.interviewer = None

    async def _cmd_resume(self, log: ChatLog, args: list[str] | None = None) -> None:
        """Resume an interrupted interview."""
        if not os.getenv("OPENAI_API_KEY"):
            log.write("[#ef4444]OPENAI_API_KEY not set.[/#ef4444]\n[dim]Use /apikey <key> to set it, or export OPENAI_API_KEY[/dim]")
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
                log.write("[#f59e0b]No interview draft found. Use /init to start one.[/#f59e0b]")
                return

            # Load from draft
            self.interviewer = ProfileInterviewer(draft_path=str(INTERVIEW_DRAFT_PATH))
            loaded = self.interviewer.load_draft()

            if not loaded:
                log.write("[#ef4444]Failed to load interview draft. Use /init --new to start fresh.[/#ef4444]")
                return

            self._in_interview = True

            # Show and reset progress bar
            progress_bar = self.query_one("#interview-progress", ProgressBar)
            progress_bar.add_class("visible")
            self._update_interview_progress()

            log.write("[#10b981]Resuming interview...[/#10b981]")
            
            # Ask the LLM to recap and continue - use streaming
            self._stream_bubble = self._begin_ai_stream(log)
            self._stream_text = ""
            
            self.run_worker(
                self._stream_interview_response("[RESUME] Please briefly summarize what you've learned about me so far, then ask your next question."),
                name="interview_stream",
                exclusive=True,
            )

        except Exception as e:
            log.write(f"[#ef4444]Error resuming interview: {e}[/#ef4444]")
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
                        log.write(f"[#10b981]Partial profile saved ({partial_profile.completion_percentage():.0f}% complete)[/#10b981]")
                except Exception as e:
                    logger.warning(f"Failed to save partial profile on cancel: {e}")
                    log.write("")
                    log.write("[#f59e0b]Interview cancelled. Progress has been saved to draft.[/#f59e0b]")
                    return

            self._in_interview = False
            self.interviewer = None
            self._hide_interview_progress()
            log.write("[#f59e0b]Interview cancelled.[/#f59e0b]")
            return

        if not self.interviewer:
            log.write("[#ef4444]Interview not initialized. Run /init again.[/#ef4444]")
            self._in_interview = False
            return

        # Start streaming response - create bubble and reset state
        self._stream_bubble = self._begin_ai_stream(log)
        self._stream_text = ""
        
        # Run streaming in a worker to avoid blocking the UI
        self.run_worker(
            self._stream_interview_response(text),
            name="interview_stream",
            exclusive=True,
        )

    async def _stream_interview_response(self, user_message: str) -> None:
        """Worker coroutine that streams the interview response."""
        if not self.interviewer:
            self.post_message(StreamError(error="Interview not initialized"))
            return

        try:
            full_message = ""
            profile = None
            display_enabled = True
            marker = "[PROFILE_COMPLETE]"
            
            async for event_type, content in self.interviewer.process_response_streaming(user_message):
                if event_type == "chunk" and isinstance(content, str):
                    full_message += content

                    if not display_enabled:
                        continue

                    marker_index = full_message.find(marker)
                    if marker_index != -1:
                        display_enabled = False
                        # Post the clean text up to the marker
                        self.post_message(StreamChunk(text=full_message[:marker_index]))
                    else:
                        # Post incremental chunk
                        self.post_message(StreamChunk(text=full_message))
                        
                elif event_type == "done":
                    if isinstance(content, tuple):
                        full_message, profile = content

            # Post completion message
            self.post_message(StreamComplete(full_message=full_message, profile=profile))

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self.post_message(StreamError(error=str(e)))

    def on_stream_chunk(self, message: StreamChunk) -> None:
        """Handle streaming chunk - update the bubble text."""
        if self._stream_bubble:
            self._stream_bubble.update(message.text)
            # Scroll the bubble into view after refresh
            self.call_after_refresh(self._scroll_to_stream_bubble)

    def _scroll_to_stream_bubble(self) -> None:
        """Scroll to keep the streaming bubble visible."""
        if self._stream_bubble:
            self._stream_bubble.scroll_visible(animate=False)

    def on_stream_complete(self, message: StreamComplete) -> None:
        """Handle streaming completion - finalize UI and save profile."""
        log = self.query_one("#chat-log", ChatLog)
        
        # Update progress bar after each exchange
        self._update_interview_progress()
        
        if message.profile:
            save_profile(message.profile)
            self._in_interview = False
            self.interviewer = None
            self._hide_interview_progress()
            
            # Set progress to 100% before hiding
            try:
                progress_bar = self.query_one("#interview-progress", ProgressBar)
                progress_bar.update(progress=100)
            except Exception:
                pass
            
            log.write("[#10b981]Profile saved successfully![/#10b981]")
            
            # Show summary
            summary = message.profile.get_summary()
            lines = ["[bold #d4af37]Profile Summary:[/bold #d4af37]"]
            for key, value in summary.items():
                if value is not None:
                    lines.append(f"      {key}: {value}")
            log.write("\n".join(lines))
        
        # Clear stream state
        self._stream_bubble = None
        self._stream_text = ""

    def on_stream_error(self, message: StreamError) -> None:
        """Handle streaming error."""
        log = self.query_one("#chat-log", ChatLog)
        log.write(f"[#ef4444]Error: {message.error}[/#ef4444]\n[dim]Try again or type /cancel to exit interview[/dim]")
        
        # Clear stream state
        self._stream_bubble = None
        self._stream_text = ""

    async def _cmd_profile(self, log: ChatLog) -> None:
        """Show current profile."""
        if not profile_exists():
            log.write("[#f59e0b]No profile found. Run /init to create one.[/f59e0b]")
            return

        profile = load_profile()
        summary = profile.get_summary()
        
        lines = [f"[bold]Profile ({profile.completion_percentage():.0f}% complete)[/bold]"]
        for key, value in summary.items():
            if value is not None:
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                lines.append(f"  [#d4af37]{key}:[/#d4af37] {value}")
        
        log.write("\n".join(lines))

    async def _cmd_fetch(self, log: ChatLog, args: list[str]) -> None:
        """Fetch scholarships from sources."""
        # Create and mount progress widget
        self._fetch_progress = FetchProgress()
        await log.mount(self._fetch_progress)
        self.call_after_refresh(lambda: self._fetch_progress.scroll_visible() if self._fetch_progress else None)
        
        # Run fetch in worker to avoid blocking UI
        self.run_worker(
            self._fetch_scholarships_worker(),
            name="fetch_scholarships",
            exclusive=True,
        )

    async def _fetch_scholarships_worker(self) -> None:
        """Worker coroutine that fetches scholarships from all sources."""
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
        
        scrapers = [
            ("Fastweb", FastwebScraper),
            ("Scholarships.com", ScholarshipsComScraper),
            ("CareerOneStop", CareerOneStopScraper),
            ("IEFA", IEFAScraper),
            ("Scholars4dev", Scholars4devScraper),
        ]
        
        try:
            # Get count before
            session = next(get_session())
            before_count = session.query(func.count(Scholarship.id)).scalar() or 0
            
            for i, (name, scraper_class) in enumerate(scrapers):
                self.post_message(FetchStartSource(index=i, name=name))
                source_key = name.lower().replace(".", "_").replace(" ", "_")
                count = 0
                new_count = 0
                
                try:
                    scraper = scraper_class()
                    scholarships = await scraper.scrape()
                    count = len(scholarships) if scholarships else 0
                    
                    # Save scholarships to database
                    import hashlib
                    for s in scholarships:
                        # Generate unique ID from source + url or title
                        id_base = f"{source_key}:{s.get('url') or s.get('title', '')}"
                        scholarship_id = hashlib.sha256(id_base.encode()).hexdigest()[:64]
                        
                        # Parse amount (handle int, string like "$5,000", or range)
                        amount = s.get("amount")
                        if amount is None:
                            amount = 0
                        if isinstance(amount, str):
                            amount = int("".join(c for c in amount if c.isdigit()) or "0")
                        elif not isinstance(amount, (int, float)):
                            amount = 0
                        amount_cents = amount * 100 if amount < 10000 else amount  # Assume < 10000 is dollars
                        
                        # Parse deadline
                        deadline_val = None
                        if s.get("deadline"):
                            try:
                                from dateutil import parser as dateparser
                                deadline_val = dateparser.parse(str(s["deadline"])).date()
                            except Exception:
                                pass
                        
                        # Convert requirements list to string
                        raw_elig = s.get("requirements", [])
                        if isinstance(raw_elig, list):
                            raw_elig = "\n".join(str(r) for r in raw_elig)
                        
                        # Check if exists
                        existing = session.query(Scholarship).filter_by(id=scholarship_id).first()
                        if existing:
                            # Update last_seen_at
                            existing.last_seen_at = datetime.now()
                        else:
                            # Insert new
                            new_scholarship = Scholarship(
                                id=scholarship_id,
                                source=source_key,
                                source_id=s.get("source_id"),
                                title=s.get("title", "")[:500],
                                description=s.get("description"),
                                amount_min=amount_cents,
                                amount_max=amount_cents,
                                deadline=deadline_val,
                                application_url=s.get("url"),
                                raw_eligibility=raw_elig or None,
                            )
                            session.add(new_scholarship)
                            new_count += 1
                    
                    session.commit()
                    
                    # Log fetch
                    fetch_log = FetchLog(
                        source=source_key,
                        fetched_at=datetime.now(),
                        scholarships_found=count,
                        scholarships_new=new_count,
                    )
                    session.add(fetch_log)
                    session.commit()
                    
                    self.post_message(FetchSourceComplete(index=i, name=name, count=count))
                    
                except Exception as e:
                    logger.error(f"Fetch error for {name}: {e}")
                    try:
                        session.rollback()
                        fetch_log = FetchLog(
                            source=source_key,
                            fetched_at=datetime.now(),
                            scholarships_found=count,
                            scholarships_new=new_count,
                            errors=str(e),
                        )
                        session.add(fetch_log)
                        session.commit()
                    except Exception as log_error:
                        logger.error(f"Failed to record fetch error for {name}: {log_error}")
                    self.post_message(FetchSourceError(index=i, name=name, error=str(e)))
            
            # Get count after
            session = next(get_session())
            after_count = session.query(func.count(Scholarship.id)).scalar() or 0
            new_count = after_count - before_count
            
            self.post_message(FetchComplete(total=after_count, new_count=new_count))
            
        except Exception as e:
            logger.error(f"Fetch worker error: {e}")
            self.post_message(FetchSourceError(index=-1, name="", error=str(e)))

    def on_fetch_start_source(self, message: FetchStartSource) -> None:
        """Handle fetch source start."""
        if self._fetch_progress:
            self._fetch_progress.start_source(message.index)
            self.call_after_refresh(lambda: self._fetch_progress.scroll_visible() if self._fetch_progress else None)

    def on_fetch_source_complete(self, message: FetchSourceComplete) -> None:
        """Handle fetch source completion."""
        if self._fetch_progress:
            self._fetch_progress.complete_source(message.index, message.count)

    def on_fetch_source_error(self, message: FetchSourceError) -> None:
        """Handle fetch source error."""
        if self._fetch_progress and message.index >= 0:
            self._fetch_progress.fail_source(message.index, message.error)

    def on_fetch_complete(self, message: FetchComplete) -> None:
        """Handle fetch completion."""
        if self._fetch_progress:
            self._fetch_progress.finish()
            self.call_after_refresh(lambda: self._fetch_progress.scroll_visible() if self._fetch_progress else None)
        self._fetch_progress = None

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
        
        lines = ["[bold]Scholarship Sources[/bold]"]
        
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
            
            lines.append(f"  {name}: {status}")
            
        log.write("\n".join(lines))

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

            lines = [f"[green]Found {len(eligible)} eligible matches out of {len(scholarships_data)} total[/green]", ""]
            lines.append("[dim]Click links to open in browser[/dim]")
            lines.append("")
            
            from rich.markup import escape as markup_escape
                    
            # Display top matches
            for i, s in enumerate(eligible[:limit], 1):
                score_pct = int(s["fit_score"] * 100)
                # Safely get match percentage
                match_res = s.get("match_result", {})
                match_pct = int(match_res.get("match_percentage", 0))
                
                if score_pct >= 80:
                    score_style = "#10b981"  # Emerald
                elif score_pct >= 60:
                    score_style = "#f59e0b"  # Amber
                else:
                    score_style = "#ef4444"  # Ruby Red
                
                amount = self._format_amount(s.get("amount_min"), s.get("amount_max"))
                deadline = s.get("deadline", "Open")[:10] if s.get("deadline") else "Open"
                url = s.get("application_url", "")
                title = markup_escape(s['title'][:50])
                safe_url = ""
                if url:
                    safe_url = (
                        url.replace("\"", "%22")
                        .replace("[", "%5B")
                        .replace("]", "%5D")
                    )
                
                # Title line - make it a clickable link if URL exists
                if url:
                    lines.append(f"[bold][link=\"{safe_url}\"]{i}. {title}[/link][/bold]")
                else:
                    lines.append(f"[bold]{i}. {title}[/bold]")
                
                lines.append(f"   [{score_style}]{score_pct}% fit[/{score_style}] | Match: {match_pct}% | {amount} | Deadline: {deadline}")
                
                # Source and URL line
                source_line = f"   [dim]{s.get('source', 'Unknown')}[/dim]"
                if url:
                    # Truncate long URLs for display, escape for markup
                    display_url = url if len(url) <= 50 else url[:47] + "..."
                    display_url_escaped = markup_escape(display_url)
                    source_line += f" • [link=\"{safe_url}\"][cyan]{display_url_escaped}[/cyan][/link]"
                lines.append(source_line)
            
            if len(eligible) > limit:
                lines.append(f"[dim]...and {len(eligible) - limit} more. Use /match --limit=N to see more.[/dim]")

            log.write("\n".join(lines))

        except Exception as e:
            log.write(f"[#ef4444]Matching failed: {e}[/#ef4444]")


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
                log.write(f"[#ef4444]Scholarship not found: {scholarship_id}[/#ef4444]")
                return

            lines = []
            lines.append(f"[bold]{scholarship.title}[/bold]")
            lines.append(f"[dim]Source: {scholarship.source}[/dim]")
            lines.append("")
            
            amount = self._format_amount(scholarship.amount_min, scholarship.amount_max)
            lines.append(f"[#d4af37]Amount:[/#d4af37] {amount}")
            
            if scholarship.deadline:
                lines.append(f"[#d4af37]Deadline:[/#d4af37] {scholarship.deadline.strftime('%Y-%m-%d')}")
            else:
                lines.append("[#d4af37]Deadline:[/#d4af37] Open/Rolling")
            
            if scholarship.description:
                lines.append("")
                lines.append("[#d4af37]Description:[/#d4af37]")
                # Truncate long descriptions
                desc = scholarship.description[:500]
                for line in desc.split("\n"):
                    lines.append(f"  {line}")
                if len(scholarship.description) > 500:
                    lines.append("  ...")
            
            if scholarship.application_url:
                lines.append("")
                lines.append(f"[#d4af37]Apply:[/#d4af37] {scholarship.application_url}")

            log.write("\n".join(lines))

        except Exception as e:
            log.write(f"[#ef4444]Error: {e}[/#ef4444]")

    async def _cmd_save(self, log: ChatLog, args: list[str]) -> None:
        """Save matches to file."""
        if not profile_exists():
            log.write("[#f59e0b]No profile found. Run /init and /match first.[/f59e0b]")
            return

        # Default to data/matches.csv
        if args:
            filename = args[0]
            # If just a filename without path, put it in data/
            from pathlib import Path
            filepath = Path(filename)
            if not filepath.parent.name:  # No directory specified
                ensure_data_dir()
                filepath = DEFAULT_MATCHES_PATH.parent / filename
        else:
            ensure_data_dir()
            filepath = DEFAULT_MATCHES_PATH
        
        filename = str(filepath)
        
        # Determine format from extension
        if filename.endswith(".csv"):
            fmt = "csv"
        elif filename.endswith(".md"):
            fmt = "markdown"
        else:
            fmt = "json"

        log.write(f"[#f59e0b]Saving matches to {filename}...[/#f59e0b]")

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
                log.write("[#f59e0b]No scholarships to save. Run /fetch first.[/f59e0b]")
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
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["title", "fit_score", "amount", "deadline", "source", "application_url"])
                    writer.writeheader()
                    for s in eligible:
                        # Format amount
                        amount = ""
                        if s.get("amount_max"):
                            dollars = s["amount_max"] // 100
                            amount = f"${dollars:,}"
                        elif s.get("amount_min"):
                            dollars = s["amount_min"] // 100
                            amount = f"${dollars:,}+"
                        
                        writer.writerow({
                            "title": s["title"],
                            "fit_score": f"{int(s['fit_score'] * 100)}%",
                            "amount": amount or "Varies",
                            "deadline": s["deadline"] or "Open",
                            "source": s["source"],
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

            log.write(f"[#10b981]Saved {len(eligible)} matches to {filename}[/#10b981]")

        except Exception as e:
            log.write(f"[#ef4444]Save failed: {e}[/#ef4444]")

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

            lines = ["[bold #d4af37]Database Statistics[/bold #d4af37]"]
            lines.append(f"  Total scholarships: {total}")
            lines.append(f"  Fetches (24h): {recent_fetches}")
            lines.append("")
            lines.append("[bold #d4af37]By Source:[/bold #d4af37]")
            for source, count in by_source:
                lines.append(f"  [#a0a0a0]{source}:[/#a0a0a0] {count}")
            
            log.write("\n".join(lines))

        except Exception as e:
            log.write(f"[#ef4444]Error: {e}[/#ef4444]")

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
                log.write("[#10b981]No expired scholarships to remove.[/#10b981]")
                return

            for s in expired:
                session.delete(s)
            session.commit()
            
            log.write(f"[#10b981]Removed {count} expired scholarships.[/#10b981]")

        except Exception as e:
            log.write(f"[#ef4444]Error: {e}[/#ef4444]")

    async def _cmd_apikey(self, log: ChatLog, args: list[str]) -> None:
        """Set OpenAI API key."""
        if not args:
            current = os.getenv("OPENAI_API_KEY")
            if current:
                masked = current[:8] + "..." + current[-4:]
                log.write(f"[#10b981]API key is set: {masked}[/#10b981]")
            else:
                log.write("[#f59e0b]No API key set. Use /apikey <key> to set one.[/f59e0b]")
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
            
            log.write("[#10b981]API key set and saved to .env[/#10b981]")
        except Exception:
            log.write("[#10b981]API key set for this session.[/ #10b981]")
            log.write("[dim]Could not save to .env file[/dim]")
