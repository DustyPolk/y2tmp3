import os
import re
import unicodedata
from urllib.parse import parse_qs, urlparse


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other security issues.
    """
    # Remove any null bytes
    filename = filename.replace("\0", "")

    # Normalize unicode characters
    filename = unicodedata.normalize("NFKD", filename)

    # Remove any path components
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    # Keep only alphanumeric, spaces, hyphens, underscores, and dots
    filename = re.sub(r"[^\w\s\-\.]", "", filename)

    # Remove multiple dots to prevent extension spoofing
    filename = re.sub(r"\.{2,}", ".", filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Limit filename length
    max_length = 200  # Leave room for extension
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[: max_length - len(ext)] + ext

    # Ensure filename is not empty
    if not filename:
        filename = "download"

    # Prevent reserved filenames on Windows
    reserved_names: list[str] = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        filename = f"download_{filename}"

    return filename


def validate_youtube_url(url: str) -> bool:
    """
    Validate that the URL is a legitimate YouTube URL.
    """
    if not url or not isinstance(url, str):
        return False

    # Parse the URL
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    # Only allow HTTPS URLs for security
    if parsed.scheme != "https":
        return False

    # Check if it's from YouTube
    valid_domains: list[str] = [
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
    ]

    if parsed.hostname not in valid_domains:
        return False

    # For youtu.be URLs, the video ID is in the path
    if parsed.hostname == "youtu.be":
        video_id = parsed.path.lstrip("/")
        if not video_id or len(video_id) < 11:
            return False
    else:
        # For youtube.com URLs, check for video ID in query params
        if "/watch" in parsed.path:
            query_params: dict[str, list[str]] = parse_qs(parsed.query)
            if "v" not in query_params or not query_params["v"][0]:
                return False
        elif "/embed/" in parsed.path or "/v/" in parsed.path:
            # Embedded videos have ID in path
            pass
        else:
            return False

    return True


def secure_path_join(base_path: str, *paths: str) -> str:
    """
    Safely join paths, preventing directory traversal attacks.
    """
    # Resolve the base path to absolute
    base_path = os.path.abspath(base_path)

    # Join the paths
    joined_path = os.path.join(base_path, *paths)

    # Resolve to absolute path
    final_path = os.path.abspath(joined_path)

    # Ensure the final path is within the base path
    if not final_path.startswith(base_path + os.sep) and final_path != base_path:
        raise ValueError("Path traversal attempt detected")

    return final_path


def validate_output_directory(path: str) -> bool:
    """
    Validate that the output directory is safe to use.
    """
    if not path:
        return False

    # Resolve to absolute path
    abs_path = os.path.abspath(path)

    # Check if it exists
    if not os.path.exists(abs_path):
        return False

    # Check if it's a directory
    if not os.path.isdir(abs_path):
        return False

    # Check if we have write permissions
    if not os.access(abs_path, os.W_OK):
        return False

    # Prevent writing to sensitive system directories
    sensitive_dirs: list[str] = [
        "/etc",
        "/bin",
        "/sbin",
        "/usr/bin",
        "/usr/sbin",
        "/boot",
        "/dev",
        "/proc",
        "/sys",
        "/root",
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\ProgramData",
        "C:\\System32",
    ]

    for sensitive_dir in sensitive_dirs:
        if abs_path.startswith(sensitive_dir):
            return False

    return True
