import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .config import get_config, create_config_command
from .downloader import download_youtube_as_mp3
from .formats import (
    AudioFormat,
    AudioQuality,
    FORMAT_CONFIGS,
    QUALITY_DESCRIPTIONS,
    get_format_from_string,
    get_quality_from_string,
    get_supported_formats,
    get_supported_qualities,
)
from .playlist import PlaylistDownloader, download_from_file
from .security import validate_output_directory, validate_youtube_url
from .utils import check_ffmpeg_installed

__version__ = "1.0.0"

console = Console()


@click.command()
@click.argument("youtube_url", required=False)
@click.option(
    "-o",
    "--output",
    help="Output directory for downloaded files",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "-f",
    "--format",
    "audio_format",
    help="Audio format (mp3, flac, aac, ogg, m4a, wav)",
    type=click.Choice(get_supported_formats(), case_sensitive=False),
)
@click.option(
    "-q",
    "--quality",
    help="Audio quality (64, 128, 192, 256, 320, lossless)",
    type=click.Choice(get_supported_qualities() + ["lossless"], case_sensitive=False),
)
@click.option(
    "--list-formats",
    is_flag=True,
    help="Show supported formats and exit",
)
@click.option(
    "--list-qualities",
    is_flag=True,
    help="Show supported qualities and exit",
)
@click.option(
    "--create-config",
    metavar="PATH",
    help="Create a sample configuration file",
)
@click.option(
    "--playlist",
    is_flag=True,
    help="Download entire playlist (auto-detected for playlist URLs)",
)
@click.option(
    "--from-file",
    metavar="FILE",
    help="Download URLs from a text file (one URL per line)",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "--max-workers",
    default=3,
    help="Maximum concurrent downloads for playlists",
    type=click.IntRange(1, 10),
)
@click.version_option(version=__version__, prog_name="y2tmp3")
def main(
    youtube_url: Optional[str],
    output: Optional[str],
    audio_format: Optional[str],
    quality: Optional[str],
    list_formats: bool,
    list_qualities: bool,
    create_config: Optional[str],
    playlist: bool,
    from_file: Optional[str],
    max_workers: int,
) -> None:
    """Download YouTube videos as high-quality audio files.
    
    Supports multiple formats (MP3, FLAC, AAC, OGG, M4A, WAV) and quality levels.
    """
    if list_formats:
        show_formats()
        return

    if list_qualities:
        show_qualities()
        return

    if create_config is not None:
        create_config_command(create_config if create_config else None)
        return

    # Handle file input
    if from_file:
        handle_file_download(from_file, output, audio_format, quality, max_workers)
        return

    # Check if URL is provided when not listing formats/qualities
    if not youtube_url:
        console.print("[red]Error: YouTube URL is required[/red]")
        console.print("Use --help for usage information")
        sys.exit(1)

    # Load configuration
    config = get_config()

    # Use CLI options or fall back to config defaults
    output_dir = output or config.get_output_dir()
    format_str = audio_format or config.get_format().value
    quality_str = quality or config.get_quality().value

    # Parse format and quality
    fmt = get_format_from_string(format_str)
    qual = get_quality_from_string(quality_str)

    if not fmt:
        console.print(f"[red]Error: Unsupported format '{format_str}'[/red]")
        console.print("Use --list-formats to see supported formats")
        sys.exit(1)

    if not qual:
        console.print(f"[red]Error: Unsupported quality '{quality_str}'[/red]")
        console.print("Use --list-qualities to see supported qualities")
        sys.exit(1)

    # Validate YouTube URL
    if not validate_youtube_url(youtube_url):
        console.print("[red]Error: Invalid YouTube URL.[/red]")
        console.print(
            "Please provide a valid YouTube URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)"
        )
        sys.exit(1)

    if not check_ffmpeg_installed():
        console.print("[red]Error: ffmpeg is not installed or not in PATH.[/red]")
        console.print("Please install ffmpeg to use this tool.")
        console.print("Visit https://ffmpeg.org/download.html for installation instructions.")
        sys.exit(1)

    # Normalize output path to absolute
    output_dir = os.path.abspath(output_dir)

    if not validate_output_directory(output_dir):
        console.print("[red]Error: Invalid output directory.[/red]")
        console.print(
            "Please ensure the directory exists, is writable, and is not a system directory."
        )
        sys.exit(1)

    try:
        console.print(f"[blue]Starting download from:[/blue] {youtube_url}")
        console.print(f"[blue]Format:[/blue] {FORMAT_CONFIGS[fmt]['description']}")
        console.print(f"[blue]Quality:[/blue] {QUALITY_DESCRIPTIONS[qual]}")
        console.print(f"[blue]Output:[/blue] {output_dir}")
        console.print()

        # Check if it's a playlist URL or user requested playlist mode
        is_playlist_url = "playlist" in youtube_url or "list=" in youtube_url
        
        if playlist or is_playlist_url:
            handle_playlist_download(youtube_url, output_dir, fmt, qual, max_workers)
        else:
            title = download_youtube_as_mp3(youtube_url, output_dir, fmt, qual)
            console.print(f"[green]✓ Successfully downloaded:[/green] {title}")
            console.print(f"[green]✓ Saved to:[/green] {output_dir}")
            
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


def show_formats() -> None:
    """Display supported audio formats."""
    table = Table(title="Supported Audio Formats")
    table.add_column("Format", style="cyan")
    table.add_column("Extension", style="magenta")
    table.add_column("Description", style="green")

    for fmt in AudioFormat:
        config = FORMAT_CONFIGS[fmt]
        table.add_row(fmt.value, config["ext"], config["description"])

    console.print(table)


def show_qualities() -> None:
    """Display supported quality levels."""
    table = Table(title="Supported Quality Levels")
    table.add_column("Quality", style="cyan")
    table.add_column("Description", style="green")

    for qual in AudioQuality:
        table.add_row(qual.value, QUALITY_DESCRIPTIONS[qual])

    console.print(table)


def handle_playlist_download(
    url: str, 
    output_dir: str, 
    fmt: AudioFormat, 
    qual: AudioQuality, 
    max_workers: int
) -> None:
    """Handle playlist download with progress reporting."""
    downloader = PlaylistDownloader(output_dir, fmt, qual, max_workers)
    results = downloader.download_playlist(url)
    
    # Show summary
    console.print()
    console.print("[bold]Download Summary:[/bold]")
    console.print(f"[green]✓ Successful: {results['success']}[/green]")
    console.print(f"[red]✗ Failed: {results['failed']}[/red]")
    
    if results["errors"]:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in results["errors"][:5]:  # Show first 5 errors
            console.print(f"  {error}")
        if len(results["errors"]) > 5:
            console.print(f"  ... and {len(results['errors']) - 5} more errors")


def handle_file_download(
    file_path: str,
    output: Optional[str],
    audio_format: Optional[str],
    quality: Optional[str],
    max_workers: int,
) -> None:
    """Handle download from file."""
    # Load configuration
    config = get_config()

    # Use CLI options or fall back to config defaults
    output_dir = output or config.get_output_dir()
    format_str = audio_format or config.get_format().value
    quality_str = quality or config.get_quality().value

    # Parse format and quality
    fmt = get_format_from_string(format_str)
    qual = get_quality_from_string(quality_str)

    if not fmt:
        console.print(f"[red]Error: Unsupported format '{format_str}'[/red]")
        sys.exit(1)

    if not qual:
        console.print(f"[red]Error: Unsupported quality '{quality_str}'[/red]")
        sys.exit(1)

    # Validate output directory
    output_dir = os.path.abspath(output_dir)
    if not validate_output_directory(output_dir):
        console.print("[red]Error: Invalid output directory.[/red]")
        sys.exit(1)

    try:
        console.print(f"[blue]Downloading from file:[/blue] {file_path}")
        console.print(f"[blue]Format:[/blue] {FORMAT_CONFIGS[fmt]['description']}")
        console.print(f"[blue]Quality:[/blue] {QUALITY_DESCRIPTIONS[qual]}")
        console.print(f"[blue]Output:[/blue] {output_dir}")
        console.print()

        results = download_from_file(file_path, output_dir, fmt, qual, max_workers)
        
        # Show summary
        console.print()
        console.print("[bold]Download Summary:[/bold]")
        console.print(f"[green]✓ Successful: {results['success']}[/green]")
        console.print(f"[red]✗ Failed: {results['failed']}[/red]")
        
        if results["errors"]:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in results["errors"][:5]:
                console.print(f"  {error}")
            if len(results["errors"]) > 5:
                console.print(f"  ... and {len(results['errors']) - 5} more errors")
                
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
