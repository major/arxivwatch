# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ArXiv Watch monitors arXiv RSS feeds for new papers, downloads PDFs, generates AI summaries using Google Gemini, and sends HTML email notifications. The application runs via GitHub Actions every 6 hours.

## Development Commands

### Basic Development
- **Run application**: `make run` or `uv run python -m arxivwatch.main`
- **Run tests**: `make test` or `uv run pytest tests/ -v`
- **Run single test**: `uv run pytest tests/test_module.py::test_function -v`
- **Lint and format**: `make lint` (uses ruff with auto-fix)
- **Type check**: `make typecheck` (uses pyright)
- **Run all checks**: `make all` or `make check` (runs test, lint, typecheck)

### Dependency Management
- Uses `uv` for dependency management
- Install dependencies: `uv sync`
- Add dependency: `uv add package-name`

## Architecture

### Execution Flow

1. **main.py**: Orchestrates the entire process
   - Loads configuration from environment variables
   - Initializes all components (storage, parser, summarizer, notifier)
   - Fetches papers from RSS feeds
   - Filters out already-notified papers using state file
   - **First-run behavior**: Processes only the latest paper but marks ALL papers as seen (prevents spam on second run)
   - Downloads PDFs and extracts first N pages (configurable)
   - Generates summaries via Gemini API
   - Sends HTML email notifications
   - Saves updated state to `notified_papers.json`

2. **Component Pipeline**:
   ```
   RSSFeedParser → PaperStorage (filter) → PDF download/extract →
   PaperSummarizer (Gemini) → EmailNotifier (HTML) → PaperStorage (save)
   ```

### Key Components

- **config.py**: pydantic-settings based configuration with environment variable support
  - All config uses `ARXIV_` prefix (e.g., `ARXIV_GEMINI_API_KEY`)
  - Supports RSS shorthand expansion (`cs.AI` → full arXiv URL)
  - Can load Gemini prompt from file via `gemini_prompt_file` setting

- **rss.py**: Parses arXiv RSS feeds using feedparser, returns `Paper` objects

- **pdf.py**: Downloads PDFs from arXiv and extracts first N pages using pypdf
  - Page count configurable via `ARXIV_GEMINI_PDF_PAGES` (default: 20)
  - Returns base64-encoded PDF content

- **summarizer.py**: Google Gemini API integration
  - Requires temporary file creation (Gemini API limitation)
  - Logs token usage (input_tokens, output_tokens, total_tokens) to structlog
  - Uses file upload API for PDF documents

- **notifier.py**: SMTP email sender with HTML support
  - Converts markdown (from Gemini) to HTML using markdown library
  - Creates multipart email (plain text + rich HTML)
  - HTML includes gradient header, styled summary, and link to paper

- **storage.py**: JSON-based persistence for notified paper IDs
  - Used to prevent re-processing papers
  - Committed to git by GitHub Actions workflow

### Configuration

All configuration via environment variables with `ARXIV_` prefix. See [.env.example](.env.example) for all options.

Critical settings:
- `ARXIV_RSS_URLS`: Comma-separated list (supports shorthand like `cs.AI` or full URLs)
- `ARXIV_GEMINI_API_KEY`: Required for summaries
- `ARXIV_GEMINI_PDF_PAGES`: Number of PDF pages to send (default: 20)
- `ARXIV_SMTP_*`: Email configuration

## Type Checking Notes

When working with google-generativeai library, use `# type: ignore[import-untyped]` and `# type: ignore[attr-defined]` as needed since the library lacks type stubs.

## GitHub Actions

Workflow at [.github/workflows/watch.yml](.github/workflows/watch.yml):
- Runs every 6 hours (`0 */6 * * *`)
- Commits updated `notified_papers.json` after each run
- Uses `secrets.DOTENV` for configuration (entire .env file as secret)

## Testing

All components have comprehensive test coverage (41 tests). Tests use mocking for external dependencies (RSS feeds, HTTP requests, SMTP, Gemini API).
