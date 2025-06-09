# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

y2tmp3 is a command-line tool that downloads YouTube videos and converts them to MP3 audio files. It uses yt-dlp for downloading and requires ffmpeg for audio conversion.

## Development Setup

This project uses UV as the package manager. To set up the development environment:

```bash
# Install dependencies in development mode
uv pip install -e .

# Alternative using pip
pip install -e .
```

## Architecture

The codebase follows a simple modular structure:

- **cli.py**: Entry point and command-line interface. Handles argument parsing, validates prerequisites (ffmpeg), and orchestrates the download process.
- **downloader.py**: Core downloading logic using yt-dlp. Configures audio extraction (MP3, 192kbps) and implements progress tracking.
- **utils.py**: Utility functions, currently just ffmpeg availability check.

The flow is: CLI entry → validate prerequisites → call downloader → save MP3 file.

## Key Technical Details

- Single dependency: `yt-dlp>=2023.1.6`
- External requirement: ffmpeg must be installed on the system
- Fixed output format: MP3 at 192kbps
- Entry points: `y2tmp3` command or `python -m y2tmp3`
- Error handling for: unavailable videos, private videos, age-restricted content, network errors

## Testing and Linting

Currently, this project has no testing framework or linting tools configured. When implementing tests or linting, this will need to be set up from scratch.