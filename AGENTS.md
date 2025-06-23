# AGENTS.md

## Build/Test/Lint Commands
- **Install**: `uv pip install -e ".[dev]"` or `pip install -e ".[dev]"`
- **Run tool**: `uv run y2tmp3 <youtube_url>` or `python -m y2tmp3 <youtube_url>`
- **Run tests**: `uv run pytest` or `pytest` (with coverage: `uv run pytest --cov`)
- **Run single test**: `uv run pytest tests/test_security.py::TestSanitizeFilename::test_basic_filename -v`
- **Lint code**: `uv run ruff check .` (fix: `uv run ruff check --fix .`)
- **Format code**: `uv run ruff format .`
- **Type check**: `uv run mypy y2tmp3/`

## Code Style Guidelines
- **Imports**: Standard library first, then third-party (yt-dlp), then local imports with relative imports (`.module`)
- **Formatting**: 4-space indentation, no trailing whitespace, max line length ~90 chars
- **Types**: No type hints currently used - add if implementing new features
- **Naming**: snake_case for functions/variables, descriptive names (e.g. `download_youtube_as_mp3`, `validate_youtube_url`)
- **Error handling**: Specific exception types with descriptive messages, validate inputs early
- **Security**: Always use `shell=False` in subprocess, sanitize filenames, validate URLs/paths
- **Docstrings**: Triple quotes for functions, focus on security considerations where relevant

## Architecture
- **cli.py**: Entry point, argument parsing, validation orchestration
- **downloader.py**: Core yt-dlp integration with progress hooks and security options
- **security.py**: Input validation, filename sanitization, path traversal prevention
- **utils.py**: System utilities (ffmpeg check) with secure subprocess calls