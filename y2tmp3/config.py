"""Configuration management for y2tmp3."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from rich.console import Console

from .formats import AudioFormat, AudioQuality, get_format_from_string, get_quality_from_string

console = Console()


class Config:
    """Configuration manager for y2tmp3."""

    def __init__(self) -> None:
        self.config_data: Dict[str, Any] = {}
        self.config_file: Optional[Path] = None
        self._load_config()

    def _get_config_paths(self) -> list[Path]:
        """Get possible configuration file paths in order of preference."""
        paths = []
        
        # Current directory
        paths.append(Path.cwd() / "y2tmp3.yaml")
        paths.append(Path.cwd() / "y2tmp3.yml")
        paths.append(Path.cwd() / ".y2tmp3.yaml")
        paths.append(Path.cwd() / ".y2tmp3.yml")
        
        # User home directory
        home = Path.home()
        paths.append(home / ".y2tmp3.yaml")
        paths.append(home / ".y2tmp3.yml")
        paths.append(home / ".config" / "y2tmp3" / "config.yaml")
        paths.append(home / ".config" / "y2tmp3" / "config.yml")
        
        # System-wide (Unix-like systems)
        if os.name != "nt":
            paths.append(Path("/etc/y2tmp3/config.yaml"))
            paths.append(Path("/etc/y2tmp3/config.yml"))
        
        return paths

    def _load_config(self) -> None:
        """Load configuration from file."""
        for config_path in self._get_config_paths():
            if config_path.exists() and config_path.is_file():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        self.config_data = yaml.safe_load(f) or {}
                    self.config_file = config_path
                    console.print(f"[dim]Loaded config from: {config_path}[/dim]")
                    break
                except yaml.YAMLError as e:
                    console.print(f"[yellow]Warning: Invalid YAML in {config_path}: {e}[/yellow]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not read {config_path}: {e}[/yellow]")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config_data.get(key, default)

    def get_format(self) -> AudioFormat:
        """Get configured audio format."""
        format_str = self.get("format", "mp3")
        fmt = get_format_from_string(format_str)
        return fmt if fmt else AudioFormat.MP3

    def get_quality(self) -> AudioQuality:
        """Get configured audio quality."""
        quality_str = self.get("quality", "192")
        qual = get_quality_from_string(quality_str)
        return qual if qual else AudioQuality.HIGH

    def get_output_dir(self) -> str:
        """Get configured output directory."""
        return self.get("output_dir", os.getcwd())

    def get_max_filesize_mb(self) -> int:
        """Get maximum file size in MB."""
        return self.get("max_filesize_mb", 500)

    def get_concurrent_downloads(self) -> int:
        """Get number of concurrent downloads for playlists."""
        return self.get("concurrent_downloads", 3)

    def create_sample_config(self, path: Path) -> None:
        """Create a sample configuration file."""
        sample_config = {
            "# y2tmp3 Configuration File": None,
            "# Audio format: mp3, flac, aac, ogg, m4a, wav": None,
            "format": "mp3",
            "# Audio quality: 64, 128, 192, 256, 320, lossless": None,
            "quality": "192",
            "# Default output directory": None,
            "output_dir": str(Path.home() / "Downloads" / "y2tmp3"),
            "# Maximum file size in MB": None,
            "max_filesize_mb": 500,
            "# Number of concurrent downloads for playlists": None,
            "concurrent_downloads": 3,
            "# Additional yt-dlp options": None,
            "yt_dlp_options": {
                "writesubtitles": False,
                "writeautomaticsub": False,
                "subtitleslangs": ["en"],
            },
        }

        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]✓ Created sample config at: {path}[/green]")
        console.print("Edit this file to customize your default settings.")


def get_config() -> Config:
    """Get the global configuration instance."""
    return Config()


def create_config_command(path: Optional[str] = None) -> None:
    """Create a sample configuration file."""
    config = Config()
    
    if path:
        config_path = Path(path)
    else:
        # Default to user config directory
        config_path = Path.home() / ".config" / "y2tmp3" / "config.yaml"
    
    if config_path.exists():
        console.print(f"[yellow]Config file already exists at: {config_path}[/yellow]")
        if not click.confirm("Overwrite existing config?"):
            return
    
    config.create_sample_config(config_path)