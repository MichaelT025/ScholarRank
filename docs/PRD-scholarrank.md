# Product Requirements Document (PRD)

# ScholarRank

**Version**: 1.0

**Author**: Planning Session

**Date**: January 20, 2026

**Status**: Draft - Pending User Review

---

## 1. Executive Summary

**ScholarRank** is a personal TUI tool that aggregates scholarship data from multiple sources, uses AI to parse eligibility requirements, and matches scholarships against the user's profile to surface the best opportunities ranked by fit score.

### The Problem

- Scholarship databases are fragmented across 30+ websites
- Each site has different UX, filters, and data formats
- Eligibility requirements are buried in unstructured text
- Students waste hours manually checking if they qualify
- High-value scholarships go unnoticed in the noise

### The Solution

A single tool that:

1. **Scrapes** scholarship data from 15+ sources
2. **Parses** eligibility using LLM extraction
3. **Matches** against your profile automatically
4. **Ranks** by fit score, deadline, and ROI

---

## 2. Target User

| Attribute           | Value                         |
| ------------------- | ----------------------------- |
| **User Type**       | Current undergraduate student |
| **Usage**           | Personal use only             |
| **Technical Level** | Comfortable with CLI tools    |
| **Budget**          | $10-20/month for LLM API      |

### User Goals

- Find scholarships I'm actually eligible for
- Prioritize high-value, low-competition opportunities
- Never miss a deadline
- Minimize time spent searching manually

---

## 3. Data Sources (Streamlined)

### Category A: General Aggregators (Largest Databases)

These are the big players with millions of scholarships. Essential for broad coverage.

| #  | Source                      | URL                        | Est. Scholarships | Scrapability | Notes                  |
| -- | --------------------------- | -------------------------- | ----------------- | ------------ | ---------------------- |
| 1  | **Fastweb**                 | fastweb.com                | 1.5M+ ($3.4B)     | Moderate     | **Has Public API**     |
| 2  | **Scholarships.com**        | scholarships.com           | 3.7M+ ($19B)      | HIGH         | Largest directory      |
| 3  | **Peterson's**              | petersons.com              | 1.9M+             | Moderate     | Includes intl guides   |
| 4  | **Unigo**                   | unigo.com                  | 3.6M+             | Moderate     | Creative scholarships  |
| 5  | **Going Merry**             | goingmerry.com             | 70,000+ ($900M)   | Moderate     | Includes local         |
| 6  | **CareerOneStop**           | careeronestop.org          | 9,500+            | HIGH         | **US Govt source**     |
| 7  | **BigFuture**               | bigfuture.collegeboard.org | 24,000+           | Moderate     | College Board official |
| 8  | **CollegeScholarships.org** | collegescholarships.org    | 5,000+            | HIGH         | Simple HTML            |
| 9  | **College Raptor**          | collegeraptor.com          | 20,000+           | Moderate     | Good filters           |
| 10 | **Chegg Scholarships**      | chegg.com/scholarships     | 25,000+           | Moderate     | Major platform         |

### Category B: International Students (→ US)

**PRIORITY FOR MVP** - Scholarships for international students studying in the US.

| #  | Source                        | URL                           | Focus                  | Scrapability | Notes             |
| -- | ----------------------------- | ----------------------------- | ---------------------- | ------------ | ----------------- |
| 11 | **IEFA**                      | iefa.org                      | International → US     | HIGH         | Premier source    |
| 12 | **InternationalScholarships** | internationalscholarships.com | International → US     | HIGH         | Good HTML         |
| 13 | **Scholars4dev**              | scholars4dev.com              | Global South → US      | HIGH         | Development focus |
| 14 | **EducationUSA**              | educationusa.state.gov        | International → US     | Moderate     | US State Dept     |
| 15 | **IIE (Fulbright)**           | iie.org                       | International exchange | Moderate     | Fulbright + more  |

### Category C: Secondary Aggregators (Expand Later)

Good coverage but lower priority or harder to scrape.

| #  | Source                     | URL                      | Notes                  | Scrapability     |
| -- | -------------------------- | ------------------------ | ---------------------- | ---------------- |
| 16 | **CollegeXpress**          | collegexpress.com        | General + college info | Moderate         |
| 17 | **Appily (Cappex)**        | appily.com               | $11B database          | LOW (SPA)        |
| 18 | **Bold.org**               | bold.org                 | Exclusive scholarships | LOW (Cloudflare) |
| 19 | **Niche**                  | niche.com                | Large database         | LOW (DataDome)   |
| 20 | **Scholarships360**        | scholarships360.org      | Highly vetted          | LOW (JS)         |
| 21 | **ScholarshipOwl**         | scholarshipowl.com       | Auto-apply platform    | LOW              |
| 22 | **JLV College Counseling** | jlvcollegecounseling.com | Identity-based lists   | HIGH             |
| 23 | **U.S. News**              | usnews.com/scholarships  | Clean interface        | Moderate         |

### Category D: Deferred Sources (Field-Specific, Demographic, etc.)

Highly specialized - add based on user profile needs.

| Type               | Examples                       | When to Add                 |
| ------------------ | ------------------------------ | --------------------------- |
| **Demographic**    | MALDEF, UNCF, HSF, HRC, APIASF | If user matches demographic |
| **Field-Specific** | Nurse.org, AccessLex, AIGA     | If user in that field       |
| **Graduate/PhD**   | ProFellow, UChicago Grad       | If user is grad student     |
| **State/Local**    | Edvisors, CoF Locator          | For state-specific matches  |
| **Organization**   | Elks, Rotary, Legion           | Based on affiliations       |

---

### Source Priority Matrix (For Implementation)

| Phase        | Sources                                                                                                   | Count | Focus                               |
| ------------ | --------------------------------------------------------------------------------------------------------- | ----- | ----------------------------------- |
| **MVP**      | Fastweb (API), Scholarships.com, CareerOneStop, **IEFA**, **InternationalScholarships**, **Scholars4dev** | 6     | Core aggregators + International→US |
| **Phase 2**  | BigFuture, Going Merry, Peterson's, CollegeScholarships.org, EducationUSA                                 | 5     | Expand general coverage             |
| **Phase 3**  | Unigo, College Raptor, Chegg, JLV, U.S. News                                                              | 5     | Secondary aggregators               |
| **Deferred** | Bold.org, Niche, demographic/field-specific                                                               | Many  | Based on user needs                 |

**MVP Focus**: General aggregators + **ALL international student sources** for comprehensive intl→US coverage.

**Total Sources**: 23 core + deferred specialized sources

---

## 4. Functional Requirements

### 4.1 Profile Management

#### FR-1: LLM-Powered Profile Interview

- **Description**: The tool conducts a conversational interview to gather user profile data
- **Behavior**:
  - LLM asks open-ended questions naturally
  - Extracts structured data from responses
  - Asks follow-up questions for missing critical fields
  - User can answer in natural language
- **Data Captured**:
  - Academic: GPA, Major, Minor, Year, Institution type
  - Location: State, City, Citizenship status
  - Demographics: Race/ethnicity, Gender, First-gen status
  - Financial: Income bracket, Need-based eligibility
  - Interests: Hobbies, Activities, Career goals
  - Special: Military affiliation, Disabilities, Religious background
  - Affiliations: Club memberships, Organizations

#### FR-2: Profile Storage

- Store profile in local JSON/YAML config file
- Support `profile show` command to display current profile
- Support `profile update` to modify specific fields via conversation

### 4.2 Data Collection

#### FR-3: Multi-Source Scraping

- **Description**: Fetch scholarship data from all configured sources
- **Behavior**:
  - Iterate through enabled sources
  - Handle API calls (Fastweb) vs HTML scraping
  - Respect rate limits (configurable delay between requests)
  - Store raw data before processing
- **Command**: `/fetch [source] [--full]`

#### FR-4: Incremental Updates

- Track last fetch timestamp per source
- Support `--full` flag to force complete re-fetch
- Default behavior: only fetch new/updated scholarships

#### FR-5: Source Health Monitoring

- Detect when a scraper breaks (site structure changed)
- Log errors with actionable messages
- Continue with other sources if one fails

### 4.3 Data Processing

#### FR-6: LLM Eligibility Extraction

- **Description**: Parse unstructured eligibility text into structured JSON
- **Input**: Raw scholarship description/requirements text
- **Output**: Structured eligibility object
- **LLM Prompt Design**: Structured extraction with JSON schema enforcement

#### FR-7: Data Normalization

- Standardize field names across sources
- Normalize dates to ISO format
- Convert amounts to integers (cents)
- Deduplicate scholarships appearing on multiple sites

### 4.4 Matching & Ranking

#### FR-8: Eligibility Matching

- **Description**: Compare user profile against scholarship eligibility
- **Logic**:
  - Hard filters: MUST match (citizenship, min GPA, etc.)
  - Soft filters: SHOULD match (preferred major, demographics)
- **Output**: Boolean eligibility + match details

#### FR-9: Fit Score Calculation

- **Formula**:
- **Criteria Match**: % of requirements satisfied
- **Deadline Urgency**: Exponential decay from deadline (higher as deadline approaches)
- **Value Density**: `award_amount / effort_score` (effort based on essay count, materials needed)
- **Competition Factor**: Inverse of estimated applicants (when available)

#### FR-10: Ranking & Filtering

- Sort by fit score (default)
- Filter by: deadline range, amount range, source, category
- Support `--limit N` to show top N results

### 4.5 Output & Display

#### FR-11: TUI Table Display (8 columns)

**Main Matches View:**
```
┌───┬─────────────────────┬────────┬──────────┬─────┬────────────┬─────────┬──────────────┐
│ # │ Scholarship         │ Amount │ Deadline │ Fit │ Source     │ Reqs    │ Status       │
├───┼─────────────────────┼────────┼──────────┼─────┼────────────┼─────────┼──────────────┤
│ 1 │ Hispanic STEM Award │ $5,000 │ Feb 15   │ 94% │ MALDEF     │ 6/6 ✓   │ Open         │
│ 2 │ First-Gen Scholars  │$10,000 │ Mar 1    │ 91% │ Fastweb    │ 5/5 ✓   │ Open         │
│ 3 │ Intl Student Grant  │ $3,000 │ Feb 28   │ 88% │ IEFA       │ 4/5 ~   │ Open         │
└───┴─────────────────────┴────────┴──────────┴─────┴────────────┴─────────┴──────────────┘
```

**Columns:**
1. **#** - Rank by fit score
2. **Scholarship** - Name (truncated with ellipsis if long)
3. **Amount** - Award amount (or range like $1K-5K)
4. **Deadline** - Date (color: red if <7 days, yellow if <30 days)
5. **Fit** - Fit score percentage (color coded: green >80%, yellow 60-80%, red <60%)
6. **Source** - Database source (abbreviated)
7. **Reqs** - Requirements match (e.g., "6/6 ✓" or "4/5 ~" for partial)
8. **Status** - Open, Closing Soon, Expired

#### FR-12: Detailed View

- Command: `/info <id>` or press Enter on selected row
- Show: Full description, all requirements, match analysis, application link
- Highlight which requirements you meet (✓) vs don't meet (✗) vs partial (~)

#### FR-13: File Export (Complete Dump)

**Supported Formats:**
- **JSON** (primary, recommended): `/save matches.json`
- **CSV** (for Excel/Sheets): `/save matches.csv`
- **Markdown** (for docs/notes): `/save matches.md`

**Export Schema (Complete Dump):**
```json
{
  "exported_at": "2026-01-20T10:30:00Z",
  "profile_summary": {
    "gpa": 3.5,
    "major": "Computer Science",
    "citizenship": "US Citizen",
    "...": "..."
  },
  "total_matches": 234,
  "scholarships": [
    {
      "id": "sch_abc123",
      "rank": 1,
      "title": "Hispanic Heritage STEM Award",
      "amount_min": 5000,
      "amount_max": 5000,
      "deadline": "2026-02-15",
      "days_until_deadline": 26,
      "application_url": "https://...",
      "source": "MALDEF",
      "source_url": "https://maldef.org/...",
      "description": "Full scholarship description text...",
      "raw_eligibility": "Original eligibility text from source...",
      "parsed_eligibility": {
        "min_gpa": 3.0,
        "majors": ["STEM", "Engineering", "Computer Science"],
        "citizenship": ["US Citizen", "Permanent Resident"],
        "demographics": ["Hispanic", "Latino"],
        "other": ["Community service involvement"]
      },
      "fit_score": 0.94,
      "fit_breakdown": {
        "criteria_match": 1.0,
        "deadline_urgency": 0.85,
        "value_density": 0.95,
        "competition_factor": 0.90
      },
      "requirements_match": {
        "total": 6,
        "matched": 6,
        "partial": 0,
        "unmatched": 0,
        "details": [
          {"requirement": "Hispanic/Latino heritage", "status": "matched", "your_value": "Mexican-American"},
          {"requirement": "GPA >= 3.0", "status": "matched", "your_value": "3.5"},
          "..."
        ]
      },
      "is_renewable": false,
      "effort_score": 3,
      "competition_score": 5,
      "tags": ["STEM", "Hispanic", "No Essay"],
      "last_updated": "2026-01-20T08:00:00Z"
    }
  ]
}
```

**CSV Export (Flattened):**
| rank | title | amount | deadline | fit_score | source | url | requirements_matched | requirements_total | is_renewable |

**Markdown Export:**
```markdown
# Scholarship Matches
Generated: 2026-01-20 | Total: 234 matches

## 1. Hispanic Heritage STEM Award
- **Amount**: $5,000
- **Deadline**: February 15, 2026 (26 days)
- **Fit Score**: 94%
- **Source**: MALDEF
- **Apply**: [Link](https://...)

### Requirements Match
- ✓ Hispanic/Latino heritage (You: Mexican-American)
- ✓ GPA >= 3.0 (You: 3.5)
- ✓ STEM major (You: Computer Science)
...
```

### 4.6 Notifications & Tracking

#### FR-14: Deadline Alerts (Future)

- Optional: Alert when deadlines approach (7 days, 3 days, 1 day)
- Out of scope for MVP

---

## 5. Non-Functional Requirements

### 5.1 Performance

- **NFR-1**: Full fetch from all Tier 1 sources < 15 minutes
- **NFR-2**: Match query against local DB < 2 seconds
- **NFR-3**: LLM extraction batched to minimize API calls

### 5.2 Reliability

- **NFR-4**: Graceful degradation if source unavailable
- **NFR-5**: Local DB persists between runs (SQLite)
- **NFR-6**: Idempotent fetches (re-running doesn't create duplicates)

### 5.3 Cost Efficiency

- **NFR-7**: Target < $20/month LLM costs at normal usage
- **NFR-8**: Cache LLM extractions (don't re-process same scholarship)
- **NFR-9**: Use cheaper models for simple tasks, expensive for complex

### 5.4 Maintainability

- **NFR-10**: Scrapers are modular (one file per source)
- **NFR-11**: Adding new source requires only new scraper module
- **NFR-12**: Config-driven source enable/disable

### 5.5 Legal & Ethical

- **NFR-13**: Respect robots.txt where specified
- **NFR-14**: Rate limit all requests (min 1 second between requests)
- **NFR-15**: No authenticated scraping (stay logged out)
- **NFR-16**: Personal use only (no redistribution of data)

---

## 6. Technical Architecture

### 6.1 Recommended Stack

| Component         | Technology                    | Rationale                              |
| ----------------- | ----------------------------- | -------------------------------------- |
| **Language**      | Python 3.11+                  | Best scraping ecosystem, LLM libraries |
| **TUI Framework** | Textual                       | Modern async TUI, beautiful out of box |
| **Scraping**      | Crawlee (Python) + Playwright | Modern, anti-bot handling built-in     |
| **HTTP Client**   | httpx                         | Async support, modern API              |
| **HTML Parsing**  | BeautifulSoup4 + lxml         | Battle-tested, fast                    |
| **Database**      | SQLite                        | Zero-config, local, portable           |
| **LLM**           | OpenAI API (gpt-4o-mini)      | Cost-effective, good at extraction     |
| **Config**        | YAML                          | Human-readable profile storage         |

### 6.2 Project Structure

```javascript
scholarrank/
├── src/
│   ├── __init__.py
│   ├── app.py                 # Textual TUI application entry point
│   ├── config.py              # Configuration management
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── screens.py         # TUI screens (main, detail, profile)
│   │   ├── widgets.py         # Custom TUI widgets
│   │   └── commands.py        # Slash command handlers
│   ├── profile/
│   │   ├── __init__.py
│   │   ├── interview.py       # LLM interview logic
│   │   └── models.py          # Profile data models
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract scraper class
│   │   ├── fastweb.py         # Fastweb API client
│   │   ├── scholarships_com.py
│   │   ├── careeronestop.py
│   │   ├── iefa.py            # International students
│   │   ├── intl_scholarships.py
│   │   ├── scholars4dev.py
│   │   └── ...                # One file per source
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── extractor.py       # LLM eligibility extraction
│   │   ├── normalizer.py      # Data normalization
│   │   └── deduplicator.py    # Cross-source deduplication
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── matcher.py         # Eligibility matching
│   │   └── scorer.py          # Fit score calculation
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py        # SQLite operations
│   │   └── models.py          # SQLAlchemy models
│   └── output/
│       ├── __init__.py
│       ├── table.py           # Rich table formatting
│       └── export.py          # CSV/JSON export
├── tests/
│   └── ...
├── config/
│   └── sources.yaml           # Source configuration
├── data/
│   ├── scholarships.db        # SQLite database
│   └── profile.yaml           # User profile
├── pyproject.toml
└── README.md
```

### 6.3 Data Model

```sql
-- Core scholarship table
CREATE TABLE scholarships (
    id TEXT PRIMARY KEY,           -- UUID or source-specific ID
    source TEXT NOT NULL,          -- 'fastweb', 'scholarships.com', etc.
    source_id TEXT,                -- Original ID from source
    title TEXT NOT NULL,
    description TEXT,
    amount_min INTEGER,            -- In cents
    amount_max INTEGER,
    deadline DATE,
    application_url TEXT,
    raw_eligibility TEXT,          -- Original text
    parsed_eligibility JSON,       -- LLM-extracted structure
    effort_score INTEGER,          -- 1-10 estimated effort
    competition_score INTEGER,     -- 1-10 estimated competition
    is_renewable BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    UNIQUE(source, source_id)
);

-- Index for common queries
CREATE INDEX idx_deadline ON scholarships(deadline);
CREATE INDEX idx_source ON scholarships(source);

-- Fetch history for incremental updates
CREATE TABLE fetch_log (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    fetched_at TIMESTAMP,
    scholarships_found INTEGER,
    scholarships_new INTEGER,
    errors TEXT
);
```

### 6.4 LLM Usage Strategy

| Task                   | Model       | Est. Cost/1000 | Caching                           |
| ---------------------- | ----------- | -------------- | --------------------------------- |
| Profile Interview      | gpt-4o      | \~$0.30        | N/A (one-time)                    |
| Eligibility Extraction | gpt-4o-mini | \~$0.015       | Yes (by content hash)             |
| Match Explanation      | gpt-4o-mini | \~$0.015       | Yes (by scholarship+profile hash) |

**Cost Estimate** (monthly):

- Initial profile: \~$0.05 (one-time)
- 2,000 scholarships extracted: \~$3.00
- 200 match explanations: \~$0.30
- **Total**: \~$3-5/month typical usage

---

## 7. TUI Interface (Terminal User Interface)

### 7.1 Overview

The application runs as an **interactive TUI** (not a one-shot CLI). Users interact via **slash commands** within a persistent terminal interface.

**Tech Stack**: Python + [Textual](https://textual.textualize.io/) (modern TUI framework)

### 7.2 Slash Commands

```javascript
/help                    Show all available commands
/init                    Run LLM interview to create/update profile
/profile                 Show current profile
/profile update          Update profile via conversation

/fetch                   Fetch from all enabled sources
/fetch fastweb           Fetch from specific source
/fetch --full            Force full re-fetch (ignore cache)
/sources                 List available sources and status

/match                   Find matching scholarships (shows in TUI)
/match --limit 20        Show top 20
/match --min 1000        Filter by minimum amount ($)
/match --days 30         Only deadlines within 30 days

/info <id>               Detailed view of scholarship
/info <id> --why         Explain why it matches

/save                    Save current matches to file (default: matches.json)
/save matches.csv        Save matches to CSV file
/save my-scholarships.json   Save matches to JSON file
/save --format md        Save as Markdown table

/stats                   Show database statistics
/clean                   Remove expired scholarships
/quit                    Exit the application
```

### 7.3 TUI Layout

The TUI features a modern, tabbed layout with a global stats bar.

```javascript
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHOLARRANK                                          [Profile: Active] │
├─────────────────────────────────────────────────────────────────────────┤
│  🎓 SCHOLARRANK  [■■■■■■■■■□ 90%]                2,807 scholarships      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [ Best Matches (42) ] [ All Results (234) ] [ Saved (0) ]              │
│  ───────────────────────────────────────────────────────────────────    │
│  │ # │ Scholarship                  │ Amount │ Deadline │ Fit │ Status ││
│  ├───┼──────────────────────────────┼────────┼──────────┼─────┼────────┤│
│  │ 1 │ Hispanic Heritage STEM Award │ $5,000 │ Feb 15   │ 94% │ ✓ Elig ││
│  │ 2 │ First-Gen Scholars Program   │$10,000 │ Mar 1    │ 91% │ ✓ Elig ││
│  │ 3 │ CA Community Service Grant   │ $2,500 │ Feb 28   │ 89% │ ✓ Elig ││
│  └───┴──────────────────────────────┴────────┴──────────┴─────┴────────┘│
│                                                                         │
│  [Tab] Switch Tabs [↑/↓] Navigate [Enter] Details [s] Save [q] Quit     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ > /match                                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.4 Key Features

**Interactive Navigation:**

- Arrow keys to navigate scholarship list
- Enter to view details
- Keyboard shortcuts for common actions

**Slash Command Input:**

- Command bar at bottom of screen
- Auto-complete for commands
- Command history (up arrow)

**File Export:**

- `/save` writes current matches to file
- Supports JSON, CSV, and Markdown formats
- Includes fit score and match details

### 7.5 Example Session

```javascript
$ scholarrank
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHOLARRANK v1.0                                    [No Profile Yet]  │
├─────────────────────────────────────────────────────────────────────────┤
│  Welcome! Type /init to create your profile, or /help for commands.    │
├─────────────────────────────────────────────────────────────────────────┤
│ > /init                                                                 │
└─────────────────────────────────────────────────────────────────────────┘

  Hi! I'll ask you some questions to build your scholarship profile.

  > What year are you in school and what are you studying?
  I'm a junior studying computer science at UCLA

  > What's your GPA?
  3.5

  > Tell me about your background - heritage, interests, activities?
  I'm first-gen, Mexican-American, play guitar, volunteer at food bank

  > Are you a US citizen or permanent resident?
  US citizen, born in California

  Profile created! Type /fetch to start collecting scholarships.

> /fetch
  Fetching scholarships...
  ━━━━━━━━━━ Fastweb API           1,247 scholarships
  ━━━━━━━━━━ Scholarships.com        892 scholarships  
  ━━━━━━━━━━ CareerOneStop           423 scholarships
  ━━━━━━━━━━ IEFA                    156 scholarships
  ━━━━━━━━━━ InternationalSchol.      89 scholarships

  Processing with AI... Done! 2,807 scholarships stored.

> /match
┌─────────────────────────────────────────────────────────────────────────┐
│  TOP MATCHES (234 eligible)                          Updated: just now │
│  ───────────────────────────────────────────────────────────────────   │
│  │ # │ Scholarship                  │ Amount │ Deadline │ Fit │       │
│  ├───┼──────────────────────────────┼────────┼──────────┼─────┤       │
│  │ 1 │ Hispanic Heritage STEM Award │ $5,000 │ Feb 15   │ 94% │ ←     │
│  │ 2 │ First-Gen Scholars Program   │$10,000 │ Mar 1    │ 91% │       │
│  │ 3 │ CA Community Service Grant   │ $2,500 │ Feb 28   │ 89% │       │
│  │ 4 │ ACM Student Scholarship      │ $1,500 │ Apr 15   │ 87% │       │
│  │ 5 │ Tech Leaders of Tomorrow     │ $3,000 │ Mar 15   │ 85% │       │
│  └───┴──────────────────────────────┴────────┴──────────┴─────┘       │
│  [↑/↓] Navigate  [Enter] Details  [s] Save  [q] Quit                  │
├─────────────────────────────────────────────────────────────────────────┤
│ > /save my-scholarships.json                                           │
│   Saved 234 matches to my-scholarships.json                            │
└─────────────────────────────────────────────────────────────────────────┘

> /info 1

  HISPANIC HERITAGE STEM AWARD
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  Amount:     $5,000 (one-time)
  Deadline:   February 15, 2026 (26 days away)
  Source:     MALDEF Scholarship Guide
  
  REQUIREMENTS:                              YOUR MATCH
    ✓ Hispanic/Latino heritage               You: Mexican-American
    ✓ STEM major                             You: Computer Science  
    ✓ GPA >= 3.0                             You: 3.5
    ✓ Community service involvement          You: Food bank volunteer
  
  FIT SCORE: 94%
  Deadline Urgency:  High (26 days)
  Value Density:     High ($5,000, short application)
  Competition:       Medium (regional, ~500 applicants)

WHY THIS IS A TOP MATCH:
You're an ideal candidate - you meet every requirement perfectly.
As a first-gen Mexican-American CS student with volunteering 
experience, you're exactly who this scholarship targets.

APPLY: https://example.com/apply
```

---

## 8. Scope Definition

### 8.1 In Scope (Phased Rollout)

#### Phase 1: MVP (Core Features + 6 Essential Sources)

**Core Features:**

| Feature                    | Priority | Notes                           |
| -------------------------- | -------- | ------------------------------- |
| LLM Profile Interview      | P0       | Conversational profile setup    |
| LLM Eligibility Extraction | P0       | Parse requirements to JSON      |
| SQLite Storage             | P0       | Local, portable                 |
| Eligibility Matching       | P0       | Compare profile to requirements |
| Fit Score Ranking          | P0       | Multi-factor scoring            |
| CLI Interface              | P0       | Primary interface               |

**MVP Data Sources (6 total):**

| Source                        | Priority | Why MVP                             |
| ----------------------------- | -------- | ----------------------------------- |
| Fastweb API                   | P0       | Legitimate API, 1.5M scholarships   |
| Scholarships.com              | P0       | Largest database (3.7M)             |
| CareerOneStop                 | P0       | US Govt, most reliable              |
| **IEFA**                      | P0       | **Premier international→US source** |
| **InternationalScholarships** | P0       | **International→US, good HTML**     |
| **Scholars4dev**              | P0       | **Global South→US, development**    |

#### Phase 2: Expanded General Coverage (+5 Sources)

| Source                  | Priority | Notes                              |
| ----------------------- | -------- | ---------------------------------- |
| BigFuture               | P1       | 24,000+ College Board scholarships |
| Going Merry             | P1       | 70,000+ including local            |
| Peterson's              | P1       | 1.9M+ scholarships                 |
| CollegeScholarships.org | P1       | Simple HTML, by major/state        |
| EducationUSA            | P1       | US State Dept international source |
| CSV/JSON Export         | P1       | Data portability                   |

#### Phase 3: Secondary Aggregators (+5 Sources)

| Source                 | Priority | Notes                      |
| ---------------------- | -------- | -------------------------- |
| Unigo                  | P2       | 3.6M scholarships          |
| College Raptor         | P2       | 20,000+ with good filters  |
| Chegg Scholarships     | P2       | Major platform             |
| JLV College Counseling | P2       | Identity-based, hidden gem |
| U.S. News              | P2       | Clean interface            |

#### Deferred: Specialized Sources (Add Based on User Profile)

| Category       | Sources                          | Trigger                         |
| -------------- | -------------------------------- | ------------------------------- |
| Heavy anti-bot | Bold.org, Niche, Scholarships360 | When stealth scraping is stable |
| Demographic    | MALDEF, UNCF, HSF, HRC, APIASF   | If user matches demographic     |
| Field-specific | Nurse.org, AccessLex, AIGA       | If user in that field           |
| Graduate/PhD   | ProFellow, UChicago Grad         | If user is grad student         |
| State/Local    | Edvisors, CoF Locator            | For state-specific matches      |

### 8.2 Out of Scope (For Now)

| Feature                                | Reason                           |
| -------------------------------------- | -------------------------------- |
| Auto-application submission            | Legal gray area, complex         |
| Web/mobile interface                   | CLI sufficient for personal use  |
| Real-time notifications                | Over-engineering for MVP         |
| Multi-user support                     | Personal tool only               |
| Heavy anti-bot sites (Bold.org, Niche) | Defer until core is stable       |
| Highly specialized sources             | Add dynamically based on profile |
| Application tracking                   | Different product                |

---

## 9. Success Metrics

| Metric                   | MVP Target | Phase 2 Target | Full Target |
| ------------------------ | ---------- | -------------- | ----------- |
| Sources integrated       | 3          | 7              | 20+         |
| Scholarships scraped     | 5,000+     | 50,000+        | 500,000+    |
| Eligible matches found   | 50+        | 200+           | 500+        |
| Fit score accuracy       | 80%+       | 85%+           | 90%+        |
| Fetch time (all sources) | < 10 min   | < 20 min       | < 45 min    |
| Monthly LLM cost         | < $10      | < $20          | < $30       |
| False positives          | < 15%      | < 10%          | < 5%        |

---

## 10. Risks & Mitigations

| Risk                                  | Likelihood | Impact | Mitigation                            |
| ------------------------------------- | ---------- | ------ | ------------------------------------- |
| Site structure changes break scrapers | High       | Medium | Modular scrapers, error alerts        |
| Anti-bot blocks scraping              | Medium     | High   | Use Playwright stealth, rate limiting |
| LLM extraction errors                 | Medium     | Medium | Validation, human review of samples   |
| Fastweb API access denied             | Low        | High   | Have scraper fallback ready           |
| Cost overruns on LLM                  | Low        | Low    | Caching, batch processing             |

---

## 11. Future Enhancements (Post-MVP)

1. **More Sources**: Bold.org, Niche, GoingMerry (with anti-bot handling)
2. **Deadline Notifications**: Email/SMS alerts for approaching deadlines
3. **Application Tracking**: Mark as applied, track status
4. **Essay Bank**: Store and reuse essay components
5. **Web Dashboard**: Visual interface (optional)
6. **Scholarship Recommendations**: ML-based "you might also like"

---

## 12. Approval

| Role | Name | Date | Status         |
| ---- | ---- | ---- | -------------- |
| User |      |      | PENDING REVIEW |

---

**Next Step**: Once PRD is approved, implementation plan will be generated.
