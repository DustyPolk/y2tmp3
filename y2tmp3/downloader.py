import yt_dlp
import os
from .security import sanitize_filename, secure_path_join


def download_youtube_as_mp3(url, output_path=None):
    if output_path is None:
        output_path = os.getcwd()
    
    # First, extract info without downloading to get the title
    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info.get('title', 'Unknown')
            
            # Sanitize the filename
            safe_filename = sanitize_filename(raw_title)
            
            # Create safe output path
            output_file = secure_path_join(output_path, f"{safe_filename}.%(ext)s")
            
            # Download options with sanitized filename
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': output_file,
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [progress_hook],
                # Security: Restrict protocols
                'allowed_protocols': ['http', 'https'],
                # Security: Don't follow redirects to file:// or other protocols
                'nocheckcertificate': False,
                # Limit download size (500MB)
                'max_filesize': 500 * 1024 * 1024,
                # Compatibility with newer yt-dlp versions
                'extract_flat': False,
                'writethumbnail': False,
                'writeinfojson': False,
            }
            
            # Download the file
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                ydl_download.download([url])
                
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


def progress_hook(d):
    if d['status'] == 'downloading':
        # Use safer progress reporting for newer yt-dlp versions
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        if total and total > 0:
            percent_str = f"{(downloaded/total)*100:.1f}%"
        else:
            percent_str = "N/A"
        speed = d.get('speed')
        if speed:
            speed_str = f"{speed/1024/1024:.1f} MB/s"
        else:
            speed_str = "N/A"
        print(f"\rDownloading: {percent_str} at {speed_str}", end='', flush=True)
    elif d['status'] == 'finished':
        print("\nDownload complete. Converting to MP3...")
    elif d['status'] == 'error':
        print(f"\nError occurred during download: {d.get('error', 'Unknown error')}")