import shutil
import subprocess


def check_ffmpeg_installed() -> bool:
    """
    Check if ffmpeg is installed and available in PATH.
    Uses secure subprocess call without shell=True.
    """
    try:
        # First check using shutil.which (safest method)
        if shutil.which("ffmpeg") is not None:
            return True

        # Double-check by trying to run ffmpeg
        # Use explicit list of arguments, no shell=True
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            shell=False,  # Explicitly set to False for security
            timeout=5,  # Add timeout to prevent hanging
            check=False,  # Don't raise exception on non-zero return
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False
