import os
import subprocess
import json

def get_video_duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
    return float(subprocess.check_output(cmd).decode().strip())

def smart_cut_shorts(input_path, output_dir):
    """
    Simulates AI cutting by extracting three 20-second highlights 
    at the beginning, middle, and end of the video.
    """
    try:
        duration = get_video_duration(input_path)
        if duration < 30:
            return [] # Too short

        shorts_paths = []
        # Marks (start, duration)
        marks = [
            (5, 20), # Start highlight
            (duration/2, 20), # Middle highlight
            (duration - 25, 20) # End highlight
        ]

        for i, (start, length) in enumerate(marks):
            out_file = os.path.join(output_dir, f"short_{i}_{os.path.basename(input_path)}")
            # FFmpeg smart cut
            cmd = [
                "ffmpeg", "-ss", str(start), "-t", str(length),
                "-i", input_path,
                "-vf", "crop=ih*9/16:ih,scale=720:1280", # Make it vertical!
                "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "128k",
                "-y", out_file
            ]
            subprocess.run(cmd, check=True)
            shorts_paths.append(out_file)

        return shorts_paths
    except Exception as e:
        print(f"Smart Cut Error: {e}")
        return []
