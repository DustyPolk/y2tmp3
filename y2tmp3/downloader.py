import yt_dlp
import os


def download_youtube_as_mp3(url, output_path=None):
    if output_path is None:
        output_path = os.getcwd()
    
    output_template = os.path.join(output_path, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            return title
    except yt_dlp.utils.DownloadError as e:
        if "Video unavailable" in str(e):
            raise Exception("Video is unavailable or has been removed")
        elif "Private video" in str(e):
            raise Exception("Video is private and cannot be accessed")
        elif "age-restricted" in str(e):
            raise Exception("Video is age-restricted")
        else:
            raise Exception(f"Download failed: {str(e)}")
    except yt_dlp.utils.ExtractorError as e:
        raise Exception(f"Failed to extract video information: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        print(f"\rDownloading: {percent} at {speed}", end='', flush=True)
    elif d['status'] == 'finished':
        print("\nDownload complete. Converting to MP3...")
    elif d['status'] == 'error':
        print("\nError occurred during download.")