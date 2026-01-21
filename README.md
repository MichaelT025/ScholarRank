# ScholarRank

A TUI application that aggregates scholarships from multiple sources, uses AI to parse eligibility requirements, and matches them against your profile.

## Key Features

- **AI Extraction**: Uses GPT-4o-mini to parse unstructured eligibility text into structured attributes.
- **Smart Matching**: Evaluates eligibility with hard and soft filters (GPA, citizenship, major, etc.).
- **Fit Scoring**: Ranks scholarships based on criteria match, deadline urgency, value density, and competition.
- **Deduplication**: Automatically identifies and merges identical scholarships across different platforms.

## Installation

```bash
pip install -e .
playwright install chromium
```

## Usage

```bash
# Set your OpenAI API key
export OPENAI_API_KEY='your-key-here'

# Run the application
scholarrank
```

## Commands

| Command        | Description                                 |
| -------------- | ------------------------------------------- |
| `/init`        | Create/update your profile via AI interview |
| `/profile`     | Show current profile                        |
| `/fetch`       | Fetch scholarships from all sources         |
| `/match`       | Find matching scholarships                  |
| `/save [file]` | Export matches to JSON/CSV/Markdown         |
| `/help`        | Show all commands                           |
| `/quit`        | Exit                                        |

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

## License

Personal use only.
