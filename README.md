# ScholarRank

A TUI application that aggregates scholarships from multiple sources, uses AI to parse eligibility requirements, and matches them against your profile.

## Installation

```bash
pip install -e .
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

## Requirements

- Python 3.10+
- OpenAI API key

## License

Personal use only.
