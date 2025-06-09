import subprocess
import shutil


def check_ffmpeg_installed():
    try:
        if shutil.which('ffmpeg') is not None:
            return True
        
        result = subprocess.run(['ffmpeg', '-version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False