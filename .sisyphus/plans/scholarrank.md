# Work Plan: ScholarRank

## Context

### Original Request

Build a TUI application that scrapes scholarship databases, uses AI to parse eligibility requirements, and matches scholarships against the user's profile. Focus on international student scholarships (→US) in MVP.

### Interview Summary

**Key Decisions:**

- TUI interface with slash commands (not CLI)
- LLM-powered conversational profile interview
- 6 MVP sources: Fastweb (API), Scholarships.com, CareerOneStop, IEFA, InternationalScholarships, Scholars4dev
- Python + Textual + SQLite + OpenAI API
- Budget: $10-20/month for LLM API
- Export: JSON (primary), CSV, Markdown with complete dump

**Research Findings:**

- Fastweb has public Developer Portal API
- CareerOneStop is US Govt (reliable HTML tables)
- International sources (IEFA, InternationalScholarships, Scholars4dev) have good HTML structure
- Modern stack: Crawlee + Playwright for scraping, Textual for TUI
- LLM cost estimate: \~$3-5/month typical usage

---

## Work Objectives

### Core Objective

Build a personal TUI tool that aggregates scholarships from 6 sources, uses LLM to parse eligibility, and ranks matches by fit score.

### Concrete Deliverables

1. Working TUI application with slash commands
2. 6 working scrapers (Fastweb API + 5 HTML scrapers)
3. LLM-powered profile interview
4. LLM eligibility extraction pipeline
5. Matching engine with fit score calculation
6. Export to JSON/CSV/Markdown

### Definition of Done

- `scholarrank` command launches TUI
- `/init` runs conversational profile interview
- `/fetch` retrieves scholarships from all 6 sources
- `/match` shows 8-column table with fit scores
- `/save matches.json` exports complete dump
- All commands work without errors

### Must Have

- Textual TUI with slash command input
- Profile stored in YAML
- SQLite database for scholarships
- LLM extraction caching (don't re-process same content)
- Rate limiting for scrapers
- Error handling when source is unavailable

### Must NOT Have (Guardrails)

- No auto-application submission
- No web/mobile interface
- No authenticated scraping (stay logged out)
- No storing API keys in code (use env vars)
- No infinite retry loops on failed scrapers
- No blocking the main TUI thread during fetch

---

## Agentic Execution Strategy

### Agent Assignments

| Agent Type                       | Tasks                                            | Specialization                                                  |
| -------------------------------- | ------------------------------------------------ | --------------------------------------------------------------- |
| **Sisyphus-Junior**              | 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20 | Core development - sequential tasks                             |
| **Sisyphus-Junior (Parallel A)** | 7, 8, 9                                          | Scraper batch 1 (Fastweb, Scholarships.com, CareerOneStop)      |
| **Sisyphus-Junior (Parallel B)** | 10, 11, 12                                       | Scraper batch 2 (IEFA, InternationalScholarships, Scholars4dev) |

### Parallel Execution Windows

```javascript
TIMELINE (Estimated)
═══════════════════════════════════════════════════════════════════════════

DAY 1-2: Foundation (Sequential)
├─ [1] Project Setup ────────────────────────► 2 hours
├─ [2] Database Models ──────────────────────► 2 hours  
└─ [3] Basic TUI Shell ──────────────────────► 3 hours

DAY 2-3: Profile + Base Scraper (Partially Parallel)
├─ [4] Profile Models ───────────────────────► 2 hours  ─┐
├─ [5] LLM Interview ────────────────────────► 4 hours   │ PARALLEL
└─ [6] Base Scraper Class ───────────────────► 2 hours  ─┘

DAY 3-4: Scrapers (FULLY PARALLEL - 6 agents)
┌─────────────────────────────────────────────────────────────────────────┐
│  PARALLEL WINDOW: Launch 6 sub-agents simultaneously                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Agent A: [7] Fastweb API ─────────────────► 3 hours                    │
│  Agent B: [8] Scholarships.com ────────────► 4 hours                    │
│  Agent C: [9] CareerOneStop ───────────────► 3 hours                    │
│  Agent D: [10] IEFA ───────────────────────► 3 hours                    │
│  Agent E: [11] InternationalScholarships ──► 3 hours                    │
│  Agent F: [12] Scholars4dev ───────────────► 3 hours                    │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                     (Wait for all scrapers)
                              ▼
DAY 4-5: Processing (Sequential)
├─ [13] LLM Extraction ──────────────────────► 4 hours
└─ [14] Data Normalization ──────────────────► 2 hours

DAY 5: Matching (Sequential)
├─ [15] Eligibility Matcher ─────────────────► 3 hours
└─ [16] Fit Score Calculator ────────────────► 2 hours

DAY 6: TUI Completion (Sequential)
├─ [17] Match Display (8-col table) ─────────► 3 hours
├─ [18] Detail View ─────────────────────────► 2 hours
└─ [19] File Export ─────────────────────────► 3 hours

DAY 7: Integration (Sequential)
└─ [20] Full Integration & Polish ───────────► 4 hours

═══════════════════════════════════════════════════════════════════════════
TOTAL ESTIMATED: 7 days (with parallel scraper execution)
         WITHOUT PARALLEL: 10+ days
         TIME SAVED: ~3 days
═══════════════════════════════════════════════════════════════════════════
```

### Parallel Execution Commands

When reaching Phase 3 (Scrapers), the orchestrator should execute:

```python
# Parallel scraper execution (6 agents)
delegate_task(
    category="quick",
    prompt="Implement Fastweb API scraper per task 7 in plan",
    skills=[],
    run_in_background=True  # Task 7
)
delegate_task(
    category="quick", 
    prompt="Implement Scholarships.com scraper per task 8 in plan",
    skills=[],
    run_in_background=True  # Task 8
)
# ... repeat for tasks 9, 10, 11, 12
```

### Dependency Gates

| Gate       | Condition                      | Blocks                    |
| ---------- | ------------------------------ | ------------------------- |
| **Gate 1** | Tasks 1-3 complete             | Tasks 4-6                 |
| **Gate 2** | Task 6 (Base Scraper) complete | Tasks 7-12 (all scrapers) |
| **Gate 3** | All scrapers (7-12) complete   | Task 13 (LLM Extraction)  |
| **Gate 4** | Task 14 complete               | Tasks 15-16 (Matching)    |
| **Gate 5** | Task 16 complete               | Tasks 17-19 (TUI)         |
| **Gate 6** | Task 19 complete               | Task 20 (Integration)     |

---

## Project Timeline

### Phase Summary

| Phase                       | Tasks | Duration | Parallel? | Agent Count |
| --------------------------- | ----- | -------- | --------- | ----------- |
| **Phase 1**: Foundation     | 1-3   | 1-2 days | No        | 1           |
| **Phase 2**: Profile System | 4-5   | 1 day    | Partial   | 1-2         |
| **Phase 3**: Scrapers       | 6-12  | 1 day    | **YES**   | **6**       |
| **Phase 4**: Processing     | 13-14 | 1 day    | No        | 1           |
| **Phase 5**: Matching       | 15-16 | 0.5 day  | No        | 1           |
| **Phase 6**: TUI Completion | 17-19 | 1 day    | No        | 1           |
| **Phase 7**: Integration    | 20    | 0.5 day  | No        | 1           |

### Milestones

| Milestone                | After Task | Deliverable                        |
| ------------------------ | ---------- | ---------------------------------- |
| **M1: TUI Works**        | 3          | Basic TUI launches with /help      |
| **M2: Profile Works**    | 5          | /init runs LLM interview           |
| **M3: Scrapers Work**    | 12         | All 6 sources fetch data           |
| **M4: Processing Works** | 14         | Eligibility extracted & normalized |
| **M5: Matching Works**   | 16         | Fit scores calculated              |
| **M6: MVP Complete**     | 20         | Full workflow functional           |

---

## Verification Strategy

### Test Decision

- **Infrastructure exists**: NO (new project)
- **User wants tests**: Manual verification (TUI is visual)
- **QA approach**: Interactive TUI verification + command output checks

### Manual Verification Procedures

Each task includes specific verification steps using:

- TUI interaction (launch app, run commands)
- SQLite queries (verify data stored correctly)
- File inspection (check exports)
- LLM API call verification (check caching works)

---

## Task Flow

```javascript
Phase 1: Tasks 1-3 (Foundation)
  [1] Project Setup
       ↓
  [2] Database Models
       ↓
  [3] Basic TUI Shell
       
Phase 2: Tasks 4-5 (Profile System)
  [4] Profile Models
       ↓
  [5] LLM Interview
       
Phase 3: Tasks 6-12 (Scrapers - Parallelizable)
  [6] Base Scraper ──┬── [7] Fastweb API
                     ├── [8] Scholarships.com
                     ├── [9] CareerOneStop
                     ├── [10] IEFA
                     ├── [11] InternationalScholarships
                     └── [12] Scholars4dev
       
Phase 4: Tasks 13-14 (Processing)
  [13] LLM Extraction
        ↓
  [14] Data Normalization
        
Phase 5: Tasks 15-16 (Matching)
  [15] Eligibility Matcher
        ↓
  [16] Fit Score Calculator
        
Phase 6: Tasks 17-19 (TUI Completion)
  [17] Match Display (8-col table)
        ↓
  [18] Detail View
        ↓
  [19] File Export
        
Phase 7: Task 20 (Integration)
  [20] Full Integration & Polish
```

---

## TODOs

---

### Phase 1: Tasks 1-3 (Foundation)

- **1. Project Setup & DependenciesWhat to do**:
  - Status: Done
  - Create project structure with `src/`, `tests/`, `config/`, `data/` directories
  - Initialize with `pyproject.toml` (use Poetry or uv)
  - Install dependencies: textual, httpx, beautifulsoup4, lxml, openai, pyyaml, crawlee, playwright
  - Create `.env.example` with required env vars (OPENAI\_API\_KEY)
  - Create `.gitignore` (include data/\*.db, .env, **pycache**)
    **Must NOT do**:
  - Don't install unnecessary dependencies
  - Don't commit API keys
    **Parallelizable**: NO (first task)**References**:
  - Textual docs: <https://textual.textualize.io/getting_started/>
  - Crawlee Python: <https://crawlee.dev/python/docs/quick-start>
    **Acceptance Criteria**:
  - `poetry install` or `uv sync` completes without errors
  - `python -c "import textual; import httpx; import openai"` succeeds
  - Project structure matches PRD section 6.2
    **Commit**: YES
  - Message: `chore: initialize project with dependencies`
  - Files: `pyproject.toml`, `.gitignore`, `.env.example`, `src/__init__.py`

---

- **2. Database Models & SetupWhat to do**:
  - Status: Done
  - Create `src/storage/models.py` with SQLAlchemy models
  - Create `src/storage/database.py` with connection management
  - Define Scholarship table per PRD section 6.3
  - Define FetchLog table for tracking fetch history
  - Add migration/init function to create tables
    **Must NOT do**:
  - Don't use complex ORM patterns (keep it simple)
  - Don't add indexes we don't need yet
    **Parallelizable**: NO (depends on 1)**References**:
  - PRD Section 6.3: Data Model (exact schema)
  - SQLAlchemy Core: <https://docs.sqlalchemy.org/en/20/core/>
    **Acceptance Criteria**:
  - Running `python -c "from src.storage.database import init_db; init_db()"` creates `data/scholarships.db`
  - SQLite file contains `scholarships` and `fetch_log` tables
  - Verify with: `sqlite3 data/scholarships.db ".schema"`
    **Commit**: YES
  - Message: `feat(storage): add SQLite database models`
  - Files: `src/storage/models.py`, `src/storage/database.py`

---

- **3. Basic TUI Shell with Slash CommandsWhat to do**:
  - Status: Done
  - Create `src/app.py` as Textual application entry point
  - Create `src/tui/screens.py` with MainScreen
  - Create `src/tui/commands.py` with command parser
  - Implement command input widget at bottom of screen
  - Support `/help`, `/quit` commands initially
  - Add header with app title and profile status
    **Must NOT do**:
  - Don't implement actual command logic yet (just parse and echo)
  - Don't add complex layouts yet
    **Parallelizable**: NO (depends on 1)**References**:
  - Textual Input: <https://textual.textualize.io/widgets/input/>
  - Textual App: <https://textual.textualize.io/guide/app/>
    **Acceptance Criteria**:
  - `python -m src.app` launches TUI
  - Typing `/help` shows list of commands
  - Typing `/quit` exits the application
  - Command bar visible at bottom of screen
    **Commit**: YES
  - Message: `feat(tui): basic TUI shell with slash commands`
  - Files: `src/app.py`, `src/tui/screens.py`, `src/tui/commands.py`

---

### Phase 2: Tasks 4-5 (Profile System)

- **4. Profile Data ModelsWhat to do**:
  - Status: Done
  - Create `src/profile/models.py` with Pydantic models for profile
  - Define all profile fields: academic, location, demographics, financial, interests, affiliations
  - Create `src/config.py` for loading/saving profile to YAML
  - Store profile in `data/profile.yaml`
    **Must NOT do**:
  - Don't validate fields too strictly (LLM will extract what it can)
    **Parallelizable**: YES (with 3)**References**:
  - PRD Section 4.1: Profile fields list
  - Pydantic v2: <https://docs.pydantic.dev/latest/>
    **Acceptance Criteria**:
  - Profile model can be serialized to YAML
  - Profile can be loaded from YAML file
  - Test: Create profile in Python, save, reload, verify equal
    **Commit**: YES
  - Message: `feat(profile): add profile data models and YAML storage`
  - Files: `src/profile/models.py`, `src/config.py`

---

- **5. LLM-Powered Profile InterviewWhat to do**:
  - Status: Done
  - Create `src/profile/interview.py` with interview logic
  - Use OpenAI API to conduct conversational interview
  - Extract structured profile from conversation
  - Ask follow-up questions for missing critical fields
  - Wire up `/init` command in TUI to run interview
  - Display extracted profile in table format after completion
    **Must NOT do**:
  - Don't require all fields (gracefully handle missing data)
  - Don't make more than 10 LLM calls per interview
    **Parallelizable**: NO (depends on 4)**References**:
  - OpenAI Chat Completions: <https://platform.openai.com/docs/guides/chat>
  - PRD Section 7.5: Example interview flow
    **Acceptance Criteria**:
  - `/init` starts conversational interview in TUI
  - After 3-5 questions, profile is extracted and shown
  - Profile saved to `data/profile.yaml`
  - Re-running `/init` offers to update existing profile
    **Commit**: YES
  - Message: `feat(profile): LLM-powered interview system`
  - Files: `src/profile/interview.py`, updates to `src/tui/commands.py`

---

### Phase 3: Tasks 6-12 (Scrapers)

- **6. Base Scraper ClassWhat to do**:
  - Status: Done
  - Create `src/scrapers/base.py` with abstract BaseScraper class
  - Define interface: `fetch()`, `parse()`, `name`, `url`
  - Add rate limiting (configurable delay between requests)
  - Add error handling and retry logic (max 3 retries)
  - Add logging for scraper activity
    **Must NOT do**:
  - Don't implement infinite retries
  - Don't block on failures (fail gracefully)
    **Parallelizable**: YES (with 4, 5)**References**:
  - Crawlee Python: <https://crawlee.dev/python/docs/quick-start>
  - httpx async: <https://www.python-httpx.org/async/>
    **Acceptance Criteria**:
  - BaseScraper is abstract and cannot be instantiated directly
  - Rate limiting works (verify with timing test)
  - Errors are caught and logged, not raised
    **Commit**: YES
  - Message: `feat(scrapers): add base scraper class with rate limiting`
  - Files: `src/scrapers/base.py`

---

- **7. Fastweb API ScraperWhat to do**:
  - Create `src/scrapers/fastweb.py` extending BaseScraper
  - Research Fastweb Developer Portal API (may need to sign up)
  - Implement API client with authentication if needed
  - Parse scholarship data into standardized format
  - Handle pagination
    **Must NOT do**:
  - Don't scrape HTML if API is available
  - Don't exceed API rate limits
    **Parallelizable**: YES (with 8-12)**References**:
  - Fastweb Developer Portal: <https://developers.fastweb.it/>
  - PRD: Fastweb has 1.5M+ scholarships
    **Acceptance Criteria**:
  - Scraper fetches scholarships from Fastweb API
  - Returns list of standardized scholarship dicts
  - Test: `python -c "from src.scrapers.fastweb import FastwebScraper; s = FastwebScraper(); print(len(s.fetch()))"` returns count
    **Commit**: YES
  - Message: `feat(scrapers): add Fastweb API scraper`
  - Files: `src/scrapers/fastweb.py`

---

- **8. Scholarships.com ScraperWhat to do**:
  - Create `src/scrapers/scholarships_com.py` extending BaseScraper
  - Analyze page structure (use browser dev tools)
  - Implement HTML scraping with BeautifulSoup
  - Extract: title, amount, deadline, description, requirements, URL
  - Handle pagination
    **Must NOT do**:
  - Don't make more than 1 request per second
  - Don't scrape pages requiring login
    **Parallelizable**: YES (with 7, 9-12)**References**:
  - Scholarships.com: <https://www.scholarships.com/scholarship-search>
  - BeautifulSoup: <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>
    **Acceptance Criteria**:
  - Scraper fetches scholarships from Scholarships.com
  - Returns standardized scholarship dicts with all required fields
  - Rate limiting is respected (1+ second between requests)
    **Commit**: YES
  - Message: `feat(scrapers): add Scholarships.com HTML scraper`
  - Files: `src/scrapers/scholarships_com.py`

---

- **9. CareerOneStop ScraperWhat to do**:
  - Create `src/scrapers/careeronestop.py` extending BaseScraper
  - Scrape US Dept of Labor scholarship finder
  - Parse HTML tables (should be cleanly structured)
  - Extract all available fields
    **Must NOT do**:
  - Don't overwhelm government servers (be extra polite)
    **Parallelizable**: YES (with 7-8, 10-12)**References**:
  - CareerOneStop: <https://www.careeronestop.org/toolkit/training/find-scholarships.aspx>
  - PRD: 9,500+ scholarships, HIGH scrapability
    **Acceptance Criteria**:
  - Scraper fetches from CareerOneStop
  - Returns 1000+ scholarships (subset is fine for testing)
  - All standard fields populated
    **Commit**: YES
  - Message: `feat(scrapers): add CareerOneStop scraper (US Govt)`
  - Files: `src/scrapers/careeronestop.py`

---

- **10. IEFA Scraper (International)What to do**:
  - Create `src/scrapers/iefa.py` extending BaseScraper
  - Scrape International Education Financial Aid database
  - Focus on scholarships for international students → US
  - Handle pagination
    **Must NOT do**:
  - Don't scrape non-US destination scholarships (filter)
    **Parallelizable**: YES (with 7-9, 11-12)**References**:
  - IEFA: <https://www.iefa.org/>
  - PRD: Premier international source, HIGH scrapability
    **Acceptance Criteria**:
  - Scraper fetches from IEFA
  - Returns scholarships for international students
  - Filtered to US-destination scholarships
    **Commit**: YES
  - Message: `feat(scrapers): add IEFA scraper (international students)`
  - Files: `src/scrapers/iefa.py`

---

- **11. InternationalScholarships.com ScraperWhat to do**:
  - Create `src/scrapers/intl_scholarships.py` extending BaseScraper
  - Scrape InternationalScholarships.com
  - Focus on scholarships for studying in US
    **Must NOT do**:
  - Don't scrape study-abroad-from-US scholarships
    **Parallelizable**: YES (with 7-10, 12)**References**:
  - Site: <https://www.internationalscholarships.com>
  - PRD: HIGH scrapability, good HTML structure
    **Acceptance Criteria**:
  - Scraper fetches from InternationalScholarships.com
  - Returns scholarships for international → US
    **Commit**: YES
  - Message: `feat(scrapers): add InternationalScholarships scraper`
  - Files: `src/scrapers/intl_scholarships.py`

---

- **12. Scholars4dev ScraperWhat to do**:
  - Create `src/scrapers/scholars4dev.py` extending BaseScraper
  - Scrape Scholars4dev (Global South focus)
  - Filter for US-destination opportunities
    **Must NOT do**:
  - Don't include non-scholarship opportunities (jobs, etc.)
    **Parallelizable**: YES (with 7-11)**References**:
  - Site: <https://www.scholars4dev.com>
  - PRD: Development scholarships, HIGH scrapability
    **Acceptance Criteria**:
  - Scraper fetches from Scholars4dev
  - Returns scholarships only (not other opportunities)
    **Commit**: YES
  - Message: `feat(scrapers): add Scholars4dev scraper`
  - Files: `src/scrapers/scholars4dev.py`

---

### Phase 4: Tasks 13-14 (Processing)

- **13. LLM Eligibility ExtractionWhat to do**:
  - Create `src/processing/extractor.py`
  - Use OpenAI gpt-4o-mini to parse raw eligibility text
  - Extract structured JSON per PRD schema (min\_gpa, majors, citizenship, demographics, etc.)
  - Implement caching: hash content, check cache before calling LLM
  - Store extraction results in database
  - Batch process to minimize API calls
    **Must NOT do**:
  - Don't call LLM for same content twice (use cache)
  - Don't use expensive models (stick to gpt-4o-mini)
    **Parallelizable**: NO (depends on scrapers)**References**:
  - OpenAI Structured Outputs: <https://platform.openai.com/docs/guides/structured-outputs>
  - PRD Section 4.3: Eligibility JSON schema
    **Acceptance Criteria**:
  - Extractor parses eligibility text to JSON
  - Caching works (second call for same content doesn't hit API)
  - JSON matches PRD schema
    **Commit**: YES
  - Message: `feat(processing): LLM eligibility extraction with caching`
  - Files: `src/processing/extractor.py`

---

- **14. Data Normalization & DeduplicationWhat to do**:
  - Create `src/processing/normalizer.py`
  - Standardize field names across sources
  - Normalize dates to ISO format
  - Convert amounts to integers (cents)
  - Create `src/processing/deduplicator.py`
  - Detect duplicates across sources (same scholarship, different URLs)
  - Keep best version (most complete data)
    **Must NOT do**:
  - Don't delete data, just mark as duplicate
    **Parallelizable**: NO (depends on 13)**References**:
  - PRD Section 4.3: FR-7 Data Normalization
    **Acceptance Criteria**:
  - All dates in ISO format
  - All amounts in cents (integers)
  - Duplicates identified and linked
    **Commit**: YES
  - Message: `feat(processing): data normalization and deduplication`
  - Files: `src/processing/normalizer.py`, `src/processing/deduplicator.py`

---

### Phase 5: Tasks 15-16 (Matching)

- **15. Eligibility MatcherWhat to do**:
  - Create `src/matching/matcher.py`
  - Compare user profile against scholarship eligibility
  - Implement hard filters (must match: citizenship, min GPA)
  - Implement soft filters (should match: preferred major, demographics)
  - Return match result with details per requirement
    **Must NOT do**:
  - Don't reject on soft filter mismatches
  - Don't assume missing data means ineligible
    **Parallelizable**: NO (depends on 14)**References**:
  - PRD Section 4.4: FR-8 Eligibility Matching
    **Acceptance Criteria**:
  - Matcher returns eligible/ineligible for each scholarship
  - Match details show which requirements met/unmet
  - Partial matches tracked (e.g., 4/5 requirements)
    **Commit**: YES
  - Message: `feat(matching): eligibility matcher with hard/soft filters`
  - Files: `src/matching/matcher.py`

---

- **16. Fit Score CalculatorWhat to do**:
  - Create `src/matching/scorer.py`
  - Implement fit score formula from PRD:
    - criteria\_match\_pct \* 0.35
    - deadline\_urgency \* 0.20
    - value\_density \* 0.25
    - competition\_factor \* 0.20
  - Calculate deadline urgency (exponential decay)
  - Calculate value density (amount / effort)
  - Estimate competition factor (when available)
    **Must NOT do**:
  - Don't invent new scoring factors
    **Parallelizable**: NO (depends on 15)**References**:
  - PRD Section 4.4: FR-9 Fit Score Calculation
    **Acceptance Criteria**:
  - Fit score between 0.0 and 1.0
  - Score breakdown available for display
  - Higher deadline urgency as deadline approaches
    **Commit**: YES
  - Message: `feat(matching): fit score calculator`
  - Files: `src/matching/scorer.py`

---

### Phase 6: Tasks 17-19 (TUI Completion)

- **17. Match Display (8-Column Table)What to do**:
  - Create `src/tui/widgets.py` with MatchTable widget
  - Implement 8-column table per PRD: #, Scholarship, Amount, Deadline, Fit, Source, Reqs, Status
  - Add color coding: green (>80%), yellow (60-80%), red (<60%)
  - Add keyboard navigation (up/down arrows)
  - Wire up `/match` command
    **Must NOT do**:
  - Don't show all matches at once (paginate or virtualize)
    **Parallelizable**: NO (depends on 16)**References**:
  - Textual DataTable: <https://textual.textualize.io/widgets/data_table/>
  - PRD Section 4.5: FR-11 8-column table spec
    **Acceptance Criteria**:
  - `/match` shows 8-column table
  - Colors work (green/yellow/red)
  - Arrow keys navigate rows
  - Selected row is highlighted
    **Commit**: YES
  - Message: `feat(tui): match display with 8-column table`
  - Files: `src/tui/widgets.py`, updates to `src/tui/screens.py`

---

- **18. Scholarship Detail ViewWhat to do**:
  - Add detail view screen or modal
  - Show full scholarship info when Enter pressed
  - Display requirements with match status (✓/✗/\~)
  - Show fit score breakdown
  - Include application link
  - Wire up `/info <id>` command
    **Must NOT do**:
  - Don't open external links automatically
    **Parallelizable**: NO (depends on 17)**References**:
  - PRD Section 4.5: FR-12 Detailed View
  - PRD Section 7.5: Example detail output
    **Acceptance Criteria**:
  - Enter on row shows detail view
  - `/info 1` shows detail for first match
  - Requirements show ✓/✗/\~ with your values
  - Application link is displayed
    **Commit**: YES
  - Message: `feat(tui): scholarship detail view`
  - Files: `src/tui/screens.py`

---

- **19. File Export (JSON/CSV/Markdown)What to do**:
  - Create `src/output/export.py`
  - Implement JSON export with complete dump schema from PRD
  - Implement CSV export (flattened)
  - Implement Markdown export with sections per scholarship
  - Wire up `/save` command with format detection
  - Default to JSON if no extension
    **Must NOT do**:
  - Don't overwrite existing files without warning
    **Parallelizable**: NO (depends on 17)**References**:
  - PRD Section 4.5: FR-13 Export Schema (complete JSON structure)
    **Acceptance Criteria**:
  - `/save matches.json` creates valid JSON file
  - `/save matches.csv` creates valid CSV file
  - `/save matches.md` creates readable Markdown
  - JSON matches PRD schema exactly
    **Commit**: YES
  - Message: `feat(output): file export (JSON, CSV, Markdown)`
  - Files: `src/output/export.py`

---

### Phase 7: Task 20 (Integration)

- **20. Full Integration & PolishWhat to do**:
  - Wire up `/fetch` command to run all scrapers
  - Add progress indicator during fetch
  - Handle errors gracefully (show which sources failed)
  - Add `/sources` command to show source status
  - Add `/stats` command for database statistics
  - Add `/profile` command to show current profile
  - Test full workflow: init → fetch → match → save
  - Fix any bugs found during integration
    **Must NOT do**:
  - Don't block TUI during long operations (run async)
    **Parallelizable**: NO (final integration)**References**:
  - PRD Section 7.2: Full command list
  - PRD Section 7.5: Example session
    **Acceptance Criteria**:
  - Complete workflow works: `/init` → `/fetch` → `/match` → `/save`
  - Progress shown during fetch
  - Failed sources don't crash app
  - All slash commands work
    **Commit**: YES
  - Message: `feat: full integration and polish`
  - Files: Multiple

---

## Parallelization Summary

| Group | Tasks               | Can Run Together                 |
| ----- | ------------------- | -------------------------------- |
| A     | 7, 8, 9, 10, 11, 12 | Yes - all scrapers independent   |
| B     | 4, 5, 6             | Partially - 4 and 6 can parallel |

---

## Commit Strategy

| After Task | Message                            | Verification              |
| ---------- | ---------------------------------- | ------------------------- |
| 1          | `chore: initialize project`        | `poetry install` works    |
| 2          | `feat(storage): database models`   | Tables created            |
| 3          | `feat(tui): basic shell`           | TUI launches              |
| 4          | `feat(profile): data models`       | YAML save/load works      |
| 5          | `feat(profile): LLM interview`     | `/init` works             |
| 6          | `feat(scrapers): base class`       | Abstract class defined    |
| 7-12       | `feat(scrapers): [source]`         | Each scraper fetches data |
| 13         | `feat(processing): LLM extraction` | Eligibility parsed        |
| 14         | `feat(processing): normalization`  | Data normalized           |
| 15         | `feat(matching): matcher`          | Eligibility checked       |
| 16         | `feat(matching): scorer`           | Fit scores calculated     |
| 17         | `feat(tui): match table`           | 8-col table displays      |
| 18         | `feat(tui): detail view`           | Details shown             |
| 19         | `feat(output): export`             | Files saved               |
| 20         | `feat: integration`                | Full workflow works       |

---

## Success Criteria

### MVP Complete When:

- All 20 tasks completed
- Full workflow works without errors
- At least 1000 scholarships fetched from 6 sources
- Match results display correctly
- Export creates valid files
- LLM costs under $10 for full fetch + process cycle

### Verification Commands

```bash
# Launch TUI
scholarrank

# Full workflow
/init                    # Should complete interview
/fetch                   # Should fetch from 6 sources
/match                   # Should show matches
/save scholarships.json  # Should create file

# Verify export
python -c "import json; print(len(json.load(open('scholarships.json'))['scholarships']))"
```
