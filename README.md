# ScholarRank

A personal TUI tool that aggregates scholarship data from multiple sources, uses AI to parse eligibility requirements, and matches scholarships against your profile to surface the best opportunities ranked by fit score.

## The Problem

- Scholarship databases are fragmented across 30+ websites
- Each site has different UX, filters, and data formats
- Eligibility requirements are buried in unstructured text
- Students waste hours manually checking if they qualify
- High-value scholarships go unnoticed in the noise

## The Solution

ScholarRank is a single tool that:

1. **Scrapes** scholarship data from 6+ sources (MVP)
2. **Parses** eligibility using LLM extraction (GPT-4o-mini)
3. **Matches** against your profile automatically
4. **Ranks** by fit score, deadline, and ROI

---

## Features

### Implemented

| Feature                   | Status     | Description                                                             |
| ------------------------- | ---------- | ----------------------------------------------------------------------- |
| **TUI Interface**         | ✅ Complete | Modern terminal UI built with [Textual](https://textual.textualize.io/) |
| **Slash Commands**        | ✅ Complete | `/help`, `/init`, `/profile`, `/quit` and more                          |
| **LLM Profile Interview** | ✅ Complete | Conversational interview using GPT-4o-mini to build your profile        |
| **Profile Storage**       | ✅ Complete | YAML-based profile with academic, demographic, financial info           |
| **SQLite Database**       | ✅ Complete | Local storage for scholarships with full schema                         |
| **Scraper Framework**     | ✅ Complete | Abstract base class with rate limiting, retries, error handling         |

### Coming Soon (Phase 3+)

| Feature                        | Status         | Description                                                                             |
| ------------------------------ | -------------- | --------------------------------------------------------------------------------------- |
| **6 Scholarship Scrapers**     | 🔄 In Progress | Fastweb, Scholarships.com, CareerOneStop, IEFA, InternationalScholarships, Scholars4dev |
| **LLM Eligibility Extraction** | ⏳ Planned      | Parse requirements into structured JSON                                                 |
| **Eligibility Matching**       | ⏳ Planned      | Compare profile against scholarship requirements                                        |
| **Fit Score Ranking**          | ⏳ Planned      | Multi-factor scoring algorithm                                                          |
| **Export (JSON/CSV/MD)**       | ⏳ Planned      | Save matches to files                                                                   |

---

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ScholarRank.git
cd ScholarRank

# Install dependencies
pip install -e .

# Set your OpenAI API key
export OPENAI_API_KEY='your-key-here'
```

### Running the Application

```bash
# Option 1: Using the installed command
scholarrank

# Option 2: Running directly
python -m src.app
```

### First Run

```javascript
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHOLARRANK v0.1.0                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Welcome! Type /init to create your profile,                            │
│  or /help to see available commands.                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ > /init                                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

Type `/init` to start the profile interview. The AI will ask you about:

- Academic info (GPA, major, year, institution)
- Location (state, citizenship status)
- Demographics (ethnicity, first-gen status)
- Financial situation
- Interests and activities
- Affiliations and memberships

---

## Slash Commands

```javascript
/help              Show all available commands
/quit, /exit, /q   Exit the application

Profile Commands:
  /init            Run LLM interview to create/update profile
  /profile         Show current profile

Data Commands (Coming Soon):
  /fetch           Fetch scholarships from all sources
  /sources         List available sources and status
  /match           Find matching scholarships
  /info <id>       Show detailed scholarship info
  /save [file]     Save matches to file (JSON, CSV, or MD)

Utility Commands (Coming Soon):
  /stats           Show database statistics
  /clean           Remove expired scholarships
```

### Keyboard Shortcuts

| Key      | Action                       |
| -------- | ---------------------------- |
| `Ctrl+Q` | Quit application             |
| `Escape` | Focus command input / Cancel |
| `Enter`  | Submit command               |

---

## Example Session

```javascript
$ scholarrank

> /init

Hi! I'll ask you some questions to build your scholarship profile.

> What year are you in school and what are you studying?
I'm a junior studying computer science at UCLA

> What's your GPA?
3.5

> Tell me about your background - heritage, interests, activities?
I'm first-gen, Mexican-American, play guitar, volunteer at food bank

> Are you a US citizen or permanent resident?
US citizen, born in California

Profile created! Your profile has been saved.

> /profile
Your Profile
Completion: 45%

  name: None
  gpa: 3.5
  major: Computer Science
  year: junior
  institution: UCLA
  citizenship: us_citizen
  state: California
  first_gen: True
  ethnicity: ['Mexican-American']
```

---

## Project Structure

```javascript
scholarrank/
├── src/
│   ├── __init__.py
│   ├── app.py                 # Textual TUI application entry point
│   ├── config.py              # Profile YAML load/save
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── screens.py         # MainScreen, InterviewScreen
│   │   └── commands.py        # Slash command parser
│   ├── profile/
│   │   ├── __init__.py
│   │   ├── models.py          # Pydantic profile models
│   │   └── interview.py       # LLM-powered interview
│   ├── scrapers/
│   │   ├── __init__.py
│   │   └── base.py            # Abstract BaseScraper class
│   └── storage/
│       ├── __init__.py
│       ├── database.py        # SQLite connection management
│       └── models.py          # SQLAlchemy models
├── data/
│   ├── scholarships.db        # SQLite database (auto-created)
│   └── profile.yaml           # User profile (auto-created)
├── docs/
│   └── PRD-scholarrank.md     # Full product requirements
├── pyproject.toml
└── README.md
```

---

## Data Model

### Profile (YAML)

Your profile is stored in `data/profile.yaml` with these sections:

| Section          | Fields                                                   |
| ---------------- | -------------------------------------------------------- |
| **Academic**     | GPA, major, minor, degree level, year, institution       |
| **Location**     | Country of origin, state, citizenship status             |
| **Demographics** | Gender, ethnicity, first-generation, veteran, disability |
| **Financial**    | Income bracket, financial need, Pell eligibility         |
| **Interests**    | Career goals, hobbies, activities, volunteer work        |
| **Affiliations** | Organizations, clubs, religious/military affiliation     |

### Scholarships (SQLite)

```sql
CREATE TABLE scholarships (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    amount_min INTEGER,      -- In cents
    amount_max INTEGER,
    deadline DATE,
    application_url TEXT,
    raw_eligibility TEXT,
    parsed_eligibility JSON,
    effort_score INTEGER,
    competition_score INTEGER,
    is_renewable BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    UNIQUE(source, source_id)
);
```

---

## MVP Data Sources

| Source                        | Type | Est. Scholarships | Priority |
| ----------------------------- | ---- | ----------------- | -------- |
| **Fastweb**                   | API  | 1.5M+             | P0       |
| **Scholarships.com**          | HTML | 3.7M+             | P0       |
| **CareerOneStop**             | HTML | 9,500+            | P0       |
| **IEFA**                      | HTML | International→US  | P0       |
| **InternationalScholarships** | HTML | International→US  | P0       |
| **Scholars4dev**              | HTML | Global South→US   | P0       |

---

## Architecture

### Technology Stack

| Component | Technology            | Rationale                    |
| --------- | --------------------- | ---------------------------- |
| Language  | Python 3.11+          | Best scraping ecosystem      |
| TUI       | Textual               | Modern async TUI framework   |
| Scraping  | httpx + BeautifulSoup | Async HTTP, reliable parsing |
| Database  | SQLite + SQLAlchemy   | Zero-config, portable        |
| LLM       | OpenAI GPT-4o-mini    | Cost-effective extraction    |
| Config    | YAML                  | Human-readable profiles      |

### Scraper Framework

All scrapers extend the `BaseScraper` class which provides:

- **Rate limiting**: Configurable delay between requests (default: 1s)
- **Retry logic**: Exponential backoff, max 3 retries
- **Error handling**: Graceful degradation, never crashes
- **Async HTTP**: Non-blocking requests with httpx

```python
from src.scrapers.base import BaseScraper

class MyScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "my_source"
    
    @property
    def base_url(self) -> str:
        return "https://example.com/scholarships"
    
    async def parse(self, response: str) -> list[dict]:
        # Parse HTML and return scholarship dicts
        ...
```

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Adding a New Scraper

1. Create `src/scrapers/your_source.py`
2. Extend `BaseScraper`
3. Implement `name`, `base_url`, and `parse()` methods
4. Register in `src/scrapers/__init__.py`

### LLM Costs

| Task                   | Model       | Est. Cost                  |
| ---------------------- | ----------- | -------------------------- |
| Profile Interview      | gpt-4o-mini | \~$0.05/interview          |
| Eligibility Extraction | gpt-4o-mini | \~$0.015/1000 scholarships |
| **Monthly Total**      |             | \~$3-5/month typical       |

---

## Roadmap

### Phase 1: Foundation ✅

- Project setup with dependencies
- SQLite database models
- Basic TUI shell with slash commands

### Phase 2: Profile System ✅

- Pydantic profile models
- YAML profile storage
- LLM-powered interview
- Base scraper class

### Phase 3: Scrapers (In Progress)

- Fastweb API scraper
- Scholarships.com scraper
- CareerOneStop scraper
- IEFA scraper
- InternationalScholarships scraper
- Scholars4dev scraper

### Phase 4-7: Processing & Matching

- LLM eligibility extraction
- Data normalization
- Eligibility matching
- Fit score calculation
- Match display (8-column table)
- Detail view
- File export (JSON/CSV/MD)
- Full integration

---

## License

Personal use only. Not for redistribution.

---

## Acknowledgments

- [Textual](https://textual.textualize.io/) - Beautiful TUI framework
- [OpenAI](https://openai.com/) - GPT models for interview and extraction
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Pydantic](https://pydantic.dev/) - Data validation
