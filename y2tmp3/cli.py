import argparse
import sys
import os
from .downloader import download_youtube_as_mp3
from .utils import check_ffmpeg_installed


__version__ = "1.0.0"


def main():
    parser = argparse.ArgumentParser(
        prog='y2tmp3',
        description='Download YouTube videos as MP3 files'
    )
    
    parser.add_argument(
        'youtube_url',
        help='The URL of the YouTube video to download'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output directory for the downloaded MP3 file (default: current directory)',
        default=os.getcwd()
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    if not check_ffmpeg_installed():
        print("Error: ffmpeg is not installed or not in PATH.")
        print("Please install ffmpeg to use this tool.")
        print("Visit https://ffmpeg.org/download.html for installation instructions.")
        sys.exit(1)
    
    if not os.path.exists(args.output):
        print(f"Error: Output directory '{args.output}' does not exist.")
        sys.exit(1)
    
    if not os.access(args.output, os.W_OK):
        print(f"Error: No write permission for directory '{args.output}'.")
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