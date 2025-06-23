"""Playlist and batch download functionality."""

import asyncio
import concurrent.futures
from pathlib import Path
from typing import List, Optional

import yt_dlp
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.table import Table

from .downloader import download_youtube_as_mp3
from .formats import AudioFormat, AudioQuality
from .security import validate_youtube_url

console = Console()


class PlaylistDownloader:
    """Handle playlist and batch downloads."""

    def __init__(
        self,
        output_dir: str,
        audio_format: AudioFormat,
        quality: AudioQuality,
        max_workers: int = 3,
    ) -> None:
        self.output_dir = output_dir
        self.audio_format = audio_format
        self.quality = quality
        self.max_workers = max_workers

    def extract_playlist_info(self, url: str) -> List[dict]:
        """Extract playlist information without downloading."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,  # Only extract metadata, don't download
            "playlistend": 100,  # Limit to first 100 videos for safety
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if "entries" not in info:
                    # Single video, not a playlist
                    return [info]
                
                # Filter out None entries and extract video info
                videos = []
                for entry in info["entries"]:
                    if entry and entry.get("id"):
                        videos.append({
                            "id": entry["id"],
                            "title": entry.get("title", "Unknown"),
                            "url": f"https://www.youtube.com/watch?v={entry['id']}",
                            "duration": entry.get("duration"),
                            "uploader": entry.get("uploader", "Unknown"),
                        })
                
                return videos
                
        except yt_dlp.DownloadError as e:
            raise Exception(f"Failed to extract playlist info: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error extracting playlist: {str(e)}")

    def download_single_video(self, video_info: dict) -> tuple[str, bool, str]:
        """Download a single video. Returns (video_id, success, message)."""
        try:
            title = download_youtube_as_mp3(
                video_info["url"], 
                self.output_dir, 
                self.audio_format, 
                self.quality
            )
            return video_info["id"], True, f"✓ {title}"
        except Exception as e:
            return video_info["id"], False, f"✗ {video_info['title']}: {str(e)}"

    def download_playlist(self, url: str, show_progress: bool = True) -> dict:
        """Download entire playlist with progress tracking."""
        console.print(f"[blue]Extracting playlist information...[/blue]")
        
        try:
            videos = self.extract_playlist_info(url)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return {"success": 0, "failed": 0, "errors": [str(e)]}

        if not videos:
            console.print("[yellow]No videos found in playlist[/yellow]")
            return {"success": 0, "failed": 0, "errors": ["No videos found"]}

        console.print(f"[green]Found {len(videos)} videos in playlist[/green]")
        
        if show_progress:
            self._show_playlist_preview(videos)

        # Download videos concurrently
        results = {"success": 0, "failed": 0, "errors": []}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Downloading playlist...", total=len(videos))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all download tasks
                future_to_video = {
                    executor.submit(self.download_single_video, video): video 
                    for video in videos
                }
                
                # Process completed downloads
                for future in concurrent.futures.as_completed(future_to_video):
                    video = future_to_video[future]
                    try:
                        video_id, success, message = future.result()
                        if success:
                            results["success"] += 1
                            if show_progress:
                                console.print(f"[green]{message}[/green]")
                        else:
                            results["failed"] += 1
                            results["errors"].append(message)
                            if show_progress:
                                console.print(f"[red]{message}[/red]")
                    except Exception as e:
                        results["failed"] += 1
                        error_msg = f"✗ {video['title']}: Unexpected error: {str(e)}"
                        results["errors"].append(error_msg)
                        if show_progress:
                            console.print(f"[red]{error_msg}[/red]")
                    
                    progress.advance(task)

        return results

    def _show_playlist_preview(self, videos: List[dict]) -> None:
        """Show a preview of the playlist contents."""
        table = Table(title="Playlist Contents")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="green")
        table.add_column("Uploader", style="blue")
        table.add_column("Duration", style="magenta")

        # Show first 10 videos
        for i, video in enumerate(videos[:10], 1):
            duration = self._format_duration(video.get("duration"))
            table.add_row(
                str(i),
                video["title"][:50] + "..." if len(video["title"]) > 50 else video["title"],
                video["uploader"][:20] + "..." if len(video["uploader"]) > 20 else video["uploader"],
                duration,
            )

        if len(videos) > 10:
            table.add_row("...", f"... and {len(videos) - 10} more videos", "", "")

        console.print(table)
        console.print()

    def _format_duration(self, duration: Optional[int]) -> str:
        """Format duration in seconds to MM:SS format."""
        if duration is None:
            return "Unknown"
        
        minutes = duration // 60
        seconds = duration % 60
        return f"{minutes}:{seconds:02d}"


def download_from_file(
    file_path: str,
    output_dir: str,
    audio_format: AudioFormat,
    quality: AudioQuality,
    max_workers: int = 3,
) -> dict:
    """Download videos from a text file containing URLs."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        raise Exception(f"Could not read file {file_path}: {str(e)}")

    if not urls:
        console.print("[yellow]No URLs found in file[/yellow]")
        return {"success": 0, "failed": 0, "errors": ["No URLs found"]}

    console.print(f"[green]Found {len(urls)} URLs in file[/green]")

    # Validate URLs
    valid_urls = []
    for url in urls:
        if validate_youtube_url(url):
            valid_urls.append(url)
        else:
            console.print(f"[yellow]Skipping invalid URL: {url}[/yellow]")

    if not valid_urls:
        console.print("[red]No valid YouTube URLs found[/red]")
        return {"success": 0, "failed": 0, "errors": ["No valid URLs"]}

    console.print(f"[blue]Downloading {len(valid_urls)} valid URLs...[/blue]")

    # Use playlist downloader for batch processing
    downloader = PlaylistDownloader(output_dir, audio_format, quality, max_workers)
    
    # Create fake video info for batch processing
    videos = [{"id": f"url_{i}", "title": url, "url": url} for i, url in enumerate(valid_urls)]
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Downloading from file...", total=len(videos))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_video = {
                executor.submit(downloader.download_single_video, video): video 
                for video in videos
            }
            
            for future in concurrent.futures.as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    video_id, success, message = future.result()
                    if success:
                        results["success"] += 1
                        console.print(f"[green]{message}[/green]")
                    else:
                        results["failed"] += 1
                        results["errors"].append(message)
                        console.print(f"[red]{message}[/red]")
                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"✗ {video['url']}: Unexpected error: {str(e)}"
                    results["errors"].append(error_msg)
                    console.print(f"[red]{error_msg}[/red]")
                
                progress.advance(task)

    return results