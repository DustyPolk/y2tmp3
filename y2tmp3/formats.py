"""Audio format definitions and utilities."""

from enum import Enum
from typing import Dict, List, Optional


class AudioFormat(Enum):
    """Supported audio formats."""

    MP3 = "mp3"
    FLAC = "flac"
    AAC = "aac"
    OGG = "ogg"
    M4A = "m4a"
    WAV = "wav"


class AudioQuality(Enum):
    """Supported audio quality levels."""

    LOW = "64"  # 64 kbps
    MEDIUM = "128"  # 128 kbps
    HIGH = "192"  # 192 kbps
    VERY_HIGH = "256"  # 256 kbps
    BEST = "320"  # 320 kbps
    LOSSLESS = "0"  # Best available (lossless when possible)


# Format-specific configurations
FORMAT_CONFIGS: Dict[AudioFormat, Dict[str, str]] = {
    AudioFormat.MP3: {
        "codec": "mp3",
        "ext": "mp3",
        "container": "mp3",
        "description": "MP3 (MPEG Audio Layer III)",
    },
    AudioFormat.FLAC: {
        "codec": "flac",
        "ext": "flac",
        "container": "flac",
        "description": "FLAC (Free Lossless Audio Codec)",
    },
    AudioFormat.AAC: {
        "codec": "aac",
        "ext": "aac",
        "container": "adts",
        "description": "AAC (Advanced Audio Coding)",
    },
    AudioFormat.OGG: {
        "codec": "vorbis",
        "ext": "ogg",
        "container": "ogg",
        "description": "OGG Vorbis",
    },
    AudioFormat.M4A: {
        "codec": "aac",
        "ext": "m4a",
        "container": "m4a",
        "description": "M4A (MPEG-4 Audio)",
    },
    AudioFormat.WAV: {
        "codec": "pcm_s16le",
        "ext": "wav",
        "container": "wav",
        "description": "WAV (Waveform Audio File Format)",
    },
}

# Quality descriptions
QUALITY_DESCRIPTIONS: Dict[AudioQuality, str] = {
    AudioQuality.LOW: "64 kbps - Low quality, small file size",
    AudioQuality.MEDIUM: "128 kbps - Standard quality",
    AudioQuality.HIGH: "192 kbps - High quality (recommended)",
    AudioQuality.VERY_HIGH: "256 kbps - Very high quality",
    AudioQuality.BEST: "320 kbps - Maximum quality",
    AudioQuality.LOSSLESS: "Best available - Lossless when possible",
}


def get_format_from_string(format_str: str) -> Optional[AudioFormat]:
    """Get AudioFormat enum from string."""
    try:
        return AudioFormat(format_str.lower())
    except ValueError:
        return None


def get_quality_from_string(quality_str: str) -> Optional[AudioQuality]:
    """Get AudioQuality enum from string."""
    # Handle both numeric strings and enum names
    quality_map = {
        "64": AudioQuality.LOW,
        "128": AudioQuality.MEDIUM,
        "192": AudioQuality.HIGH,
        "256": AudioQuality.VERY_HIGH,
        "320": AudioQuality.BEST,
        "0": AudioQuality.LOSSLESS,
        "low": AudioQuality.LOW,
        "medium": AudioQuality.MEDIUM,
        "high": AudioQuality.HIGH,
        "very_high": AudioQuality.VERY_HIGH,
        "best": AudioQuality.BEST,
        "lossless": AudioQuality.LOSSLESS,
    }
    return quality_map.get(quality_str.lower())


def get_supported_formats() -> List[str]:
    """Get list of supported format strings."""
    return [fmt.value for fmt in AudioFormat]


def get_supported_qualities() -> List[str]:
    """Get list of supported quality strings."""
    return [qual.value for qual in AudioQuality]


def build_yt_dlp_postprocessor(
    audio_format: AudioFormat, quality: AudioQuality
) -> Dict[str, str]:
    """Build yt-dlp postprocessor configuration for given format and quality."""
    config = FORMAT_CONFIGS[audio_format]

    postprocessor = {
        "key": "FFmpegExtractAudio",
        "preferredcodec": config["codec"],
    }

    # Set quality based on format capabilities
    if audio_format in [AudioFormat.FLAC, AudioFormat.WAV]:
        # Lossless formats - don't set quality
        if quality != AudioQuality.LOSSLESS:
            # For lossless formats, we can still downsample if requested
            postprocessor["preferredquality"] = quality.value
    else:
        # Lossy formats - always set quality
        if quality == AudioQuality.LOSSLESS:
            # Use best quality for lossy formats when lossless is requested
            postprocessor["preferredquality"] = AudioQuality.BEST.value
        else:
            postprocessor["preferredquality"] = quality.value

    return postprocessor