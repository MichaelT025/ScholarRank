# ScholarRank

A TUI application that aggregates scholarships from multiple sources, uses AI to parse eligibility requirements, and matches them against your profile.

## Key Features

- **Modern TUI**: Premium terminal interface with a sophisticated "Carbon & Gold" theme, tabbed views, and interactive modals.
- **AI-Powered Interview**: Conversational chat interface to build your profile naturally.
- **Smart Matching**: Evaluates eligibility with hard and soft filters (GPA, citizenship, major, etc.).
- **Fit Scoring**: Ranks scholarships based on criteria match, deadline urgency, value density, and competition.
- **Deduplication**: Automatically identifies and merges identical scholarships across different platforms.

## Prerequisites

- Python 3.10+
- OpenAI API key
- Playwright browser binaries (Chromium)

## Setup

```bash
# Optional: create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

# Install dependencies in editable mode
pip install -e .

# Install Playwright browser binaries (required for scraping)
playwright install chromium
```

## Configuration

ScholarRank uses the OpenAI API for profile interviews and eligibility parsing.

```bash
# Option 1: Set via TUI command (recommended)
scholarrank
# Then run: /apikey sk-your-key-here

# Option 2: export directly
export OPENAI_API_KEY='your-key-here'

# Option 3: create a local .env file
cp .env.example .env
```

## Initialize and Run

```bash
# Start the TUI
scholarrank
```

First-run flow in the TUI:

1. Run `/init` to complete the AI profile interview.
2. Run `/fetch` to pull scholarships from all sources.
3. Run `/match` to view ranked scholarships in a tabbed interface.
4. Run `/save` to export results to `data/matches.csv`.

## Usage

Typical daily flow:

1. `/init` if your profile changes.
2. `/fetch` to refresh sources.
3. `/match --limit 20` to view top results.
4. `/save` to export (defaults to `data/matches.csv`).

## Commands

| Command         | Description                                 |
| --------------- | ------------------------------------------- |
| `/init`         | Create/update your profile via AI interview |
| `/profile`      | Show current profile                        |
| `/fetch`        | Fetch scholarships from all sources         |
| `/sources`      | Show scholarship sources and status         |
| `/stats`        | Show database statistics                    |
| `/clean`        | Remove expired scholarships from database   |
| `/match`        | Find matching scholarships                  |
| `/save [file]`  | Export matches (default: data/matches.csv)  |
| `/apikey <key>` | Set OpenAI API key                          |
| `/help`         | Show all commands                           |
| `/quit`         | Exit                                        |

## Supported Sources

- **Fastweb**: 1.5M+ scholarships (API with fallback)
- **Scholarships.com**: 3.7M+ scholarships
- **CareerOneStop**: 9,500+ US Government source
- **IEFA**: International Education Financial Aid
- **InternationalScholarships.com**: For international students
- **Scholars4dev**: Global South & International focus

## Requirements

- Python 3.10+
- OpenAI API key

## Data Storage

- `data/profile.yaml`: Your profile created by `/init`.
- `data/scholarships.db`: Local SQLite database of scholarships.
- `data/matches.csv`: Exported scholarship matches from `/save`.
- `data/cache/`: LLM extraction cache for eligibility parsing.
- `data/fetch_errors.log`: Application log containing errors and warnings.

## Troubleshooting

- `OPENAI_API_KEY environment variable not set`: run `/apikey sk-your-key` or export the key.
- Scrapers failing to launch: rerun `playwright install chromium`.
- Empty results: run `/fetch` before `/match`.
- Persistent errors: check `data/fetch_errors.log` for detailed diagnostics.

## License

Personal use only.
