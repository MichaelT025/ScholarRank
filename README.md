# ScholarRank

LLM-powered scholarship search and ranking tool.

## Features

- **LLM Profile Interview**: Conversational interview to build your student profile using GPT-4.
- **TUI Interface**: Modern terminal user interface built with Textual.
- **Smart Matching**: (In progress) Match scholarships to your specific profile.
- **Extensible Scrapers**: (In progress) Framework for fetching scholarships from multiple sources.

## Getting Started

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY='your-key-here'
   ```

2. Run the application:
   ```bash
   python src/app.py
   ```

3. Type `/init` to start your profile interview.

## Project Structure

- `src/`: Source code
  - `tui/`: Textual interface screens and commands
  - `profile/`: Profile models and interview logic
  - `scrapers/`: Scholarship scraping framework
- `docs/`: Project documentation and PRD
- `data/`: Local storage (sqlite, yaml profiles)
