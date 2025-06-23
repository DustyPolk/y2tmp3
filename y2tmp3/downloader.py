import os
import sys
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from typing import Any, Optional

import yt_dlp
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .formats import AudioFormat, AudioQuality, build_yt_dlp_postprocessor, FORMAT_CONFIGS
from .security import sanitize_filename, secure_path_join

console = Console()

# Global progress instance for rich progress bars
progress_instance: Optional[Progress] = None
task_id: Optional[int] = None


def download_youtube_as_mp3(
    url: str,
    output_path: Optional[str] = None,
    audio_format: AudioFormat = AudioFormat.MP3,
    quality: AudioQuality = AudioQuality.HIGH,
) -> str:
    if output_path is None:
        output_path = os.getcwd()

    # First, extract info without downloading to get the title
    ydl_opts_info = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "noplaylist": True,  # Force single video extraction even if URL has playlist params
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info.get("title", "Unknown")

            # Sanitize the filename
            safe_filename = sanitize_filename(raw_title)

            # Create safe output path with correct extension
            file_ext = FORMAT_CONFIGS[audio_format]["ext"]
            output_file = secure_path_join(output_path, f"{safe_filename}.%(ext)s")

            # Build postprocessor configuration
            postprocessor = build_yt_dlp_postprocessor(audio_format, quality)

            # Download options with sanitized filename
            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [postprocessor],
                "outtmpl": output_file,
                "quiet": True,  # Suppress yt-dlp output to avoid interference with Rich progress
                "no_warnings": True,  # Suppress warnings to keep output clean
                "progress_hooks": [rich_progress_hook],
                # Security: Restrict protocols
                "allowed_protocols": ["http", "https"],
                # Security: Don't follow redirects to file:// or other protocols
                "nocheckcertificate": False,
                # Limit download size (500MB)
                "max_filesize": 500 * 1024 * 1024,
                # Compatibility with newer yt-dlp versions
                "extract_flat": False,
                "writethumbnail": False,
                "writeinfojson": False,
                "noplaylist": True,  # Force single video download even if URL has playlist params
            }

            # Download the file with rich progress bar
            global progress_instance, task_id
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=10,  # Increase refresh rate for smoother updates
            ) as progress:
                progress_instance = progress
                task_id = progress.add_task("Preparing download...", total=100, completed=0)
                
                # Suppress yt-dlp output completely to avoid interference with Rich progress
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                        ydl_download.download([url])
                
                progress_instance = None
                task_id = None

            return safe_filename
    except yt_dlp.DownloadError as e:
        if "Video unavailable" in str(e):
            raise Exception("Video is unavailable or has been removed")
        elif "Private video" in str(e):
            raise Exception("Video is private and cannot be accessed")
        elif "age-restricted" in str(e):
            raise Exception("Video is age-restricted")
        else:
            raise Exception(f"Download failed: {str(e)}")
    except yt_dlp.ExtractorError as e:
        raise Exception(f"Failed to extract video information: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


def rich_progress_hook(d: dict[str, Any]) -> None:
    """Rich progress hook for yt-dlp downloads."""
    global progress_instance, task_id
    
    if not progress_instance or task_id is None:
        return
        
    if d["status"] == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        
        if total and total > 0:
            # Update with actual progress
            progress_instance.update(task_id, completed=downloaded, total=total, description="Downloading...")
        else:
            # For unknown total size, show downloaded bytes
            downloaded_mb = downloaded / (1024 * 1024)
            progress_instance.update(task_id, description=f"Downloading... {downloaded_mb:.1f} MB")
            
    elif d["status"] == "finished":
        if progress_instance and task_id is not None:
            progress_instance.update(task_id, description="✓ Download complete, converting...")
            # Complete the progress bar
            progress_instance.update(task_id, completed=100, total=100)
            
    elif d["status"] == "error":
        if progress_instance and task_id is not None:
            error_msg = d.get("error", "Unknown error")
            progress_instance.update(task_id, description=f"✗ Error: {error_msg}")


def progress_hook(d: dict[str, Any]) -> None:
    """Legacy progress hook for backward compatibility."""
    if d["status"] == "downloading":
        # Use safer progress reporting for newer yt-dlp versions
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
        if total and total > 0:
            percent_str = f"{(downloaded / total) * 100:.1f}%"
        else:
            percent_str = "N/A"
        speed = d.get("speed")
        if speed:
            speed_str = f"{speed / 1024 / 1024:.1f} MB/s"
        else:
            speed_str = "N/A"
        print(f"\rDownloading: {percent_str} at {speed_str}", end="", flush=True)
    elif d["status"] == "finished":
        print("\nDownload complete. Converting...")
    elif d["status"] == "error":
        print(f"\nError occurred during download: {d.get('error', 'Unknown error')}")
