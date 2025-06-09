# y2tmp3

A simple command-line tool to download YouTube videos as MP3 audio files.

## Features

- Download YouTube videos and convert them to MP3 format
- Simple command-line interface
- Progress tracking during download
- Automatic handling of special characters in filenames
- Error handling for common issues (unavailable videos, network errors, etc.)

## Installation

### Prerequisites

Before installing y2tmp3, you need to have `ffmpeg` installed on your system. FFmpeg is required for audio conversion.

#### Installing ffmpeg

**Windows:**
1. Download ffmpeg from https://www.gyan.dev/ffmpeg/builds/
2. Extract the archive to a folder (e.g., `C:\ffmpeg`)
3. Add the bin folder to your PATH environment variable:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find and select "Path", then click "Edit"
   - Click "New" and add the path to ffmpeg's bin folder (e.g., `C:\ffmpeg\bin`)
   - Click "OK" to save

**macOS:**
Using Homebrew:
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Linux (Fedora):**
```bash
sudo dnf install ffmpeg
```

### Installing y2tmp3

Once ffmpeg is installed, you can install y2tmp3 using pip:

```bash
pip install y2tmp3
```

## Usage

Basic usage:
```bash
y2tmp3 <youtube_url>
```

Specify output directory:
```bash
y2tmp3 <youtube_url> -o /path/to/output/directory
```

Examples:
```bash
# Download to current directory
y2tmp3 https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Download to specific directory
y2tmp3 https://www.youtube.com/watch?v=dQw4w9WgXcQ -o ~/Music/

# Show version
y2tmp3 --version

# Show help
y2tmp3 --help
```

## Copyright Disclaimer

This tool is provided for educational and personal use only. Users are responsible for complying with YouTube's Terms of Service and respecting copyright laws. Only download content that you have permission to download.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Issues

If you encounter any problems, please file an issue on the GitHub repository.