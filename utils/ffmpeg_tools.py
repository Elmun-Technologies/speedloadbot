import ffmpeg
import os
import random
import string

def get_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def compress_video(input_path, output_path, target_size_mb=48):
    """
    Compress video using constant rate factor. 
    Simplistic approach: target <50MB for Telegram.
    """
    try:
        # Get duration
        probe = ffmpeg.probe(input_path)
        duration = float(probe['format']['duration'])
        
        # Calculate bitrate (bits per sec)
        # target_size_mb * 8 * 1024 * 1024 / duration
        target_bitrate = (target_size_mb * 8 * 1024 * 1024) / duration
        
        # Pass 1 & 2 or Just CRF?
        # Let's use CRF for speed + reasonable size
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vcodec='libx264', crf=28, preset='fast', acodec='aac', audio_bitrate='128k')
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception:
        return False

def strip_metadata(input_path, output_path):
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, map_metadata=-1, c='copy')
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception:
        return False

def extract_audio_ffmpeg(input_path, output_path):
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, qscale_a=0, map='a')
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception:
        return False

def create_gif(input_path, output_path, start_time="00:00:00", duration=5):
    try:
        (
            ffmpeg
            .input(input_path, ss=start_time, t=duration)
            .filter('fps', fps=15)
            .filter('scale', w=480, h=-1)
            .output(output_path)
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception:
        return False
