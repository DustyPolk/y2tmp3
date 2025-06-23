import argparse
import os
import sys

from .downloader import download_youtube_as_mp3
from .security import validate_output_directory, validate_youtube_url
from .utils import check_ffmpeg_installed

__version__ = "1.0.0"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="y2tmp3", description="Download YouTube videos as MP3 files"
    )

    parser.add_argument("youtube_url", help="The URL of the YouTube video to download")

    parser.add_argument(
        "-o",
        "--output",
        help="Output directory for the downloaded MP3 file (default: current directory)",
        default=os.getcwd(),
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    # Validate YouTube URL
    if not validate_youtube_url(args.youtube_url):
        print("Error: Invalid YouTube URL.")
        print(
            "Please provide a valid YouTube URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)"
        )
        sys.exit(1)

    if not check_ffmpeg_installed():
        print("Error: ffmpeg is not installed or not in PATH.")
        print("Please install ffmpeg to use this tool.")
        print("Visit https://ffmpeg.org/download.html for installation instructions.")
        sys.exit(1)

    # Normalize output path to absolute
    args.output = os.path.abspath(args.output)

    if not validate_output_directory(args.output):
        print("Error: Invalid output directory.")
        print(
            "Please ensure the directory exists, is writable, and is not a system directory."
        )
        sys.exit(1)

    try:
        print(f"Starting download from: {args.youtube_url}")
        title = download_youtube_as_mp3(args.youtube_url, args.output)
        print(f"\nSuccessfully downloaded: {title}")
        print(f"Saved to: {args.output}")
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
