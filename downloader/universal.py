import yt_dlp
import os
from config import DOWNLOAD_DIR

def extract_universal_info(url: str):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Video"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration", 0)
            }
        except Exception:
            return None
            
def download_media(url: str, quality: str, platform: str, progress_hook=None) -> dict:
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(resolution)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    if quality == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
        })
    elif quality == 'thumbnail':
        ydl_opts.update({
            'skip_download': True,
            'writethumbnail': True,
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
        })
    else:
        if platform == "youtube":
            resolution_map = {'360p': '360', '720p': '720', '1080p': '1080'}
            height = resolution_map.get(quality, '720')
            ydl_opts.update({
                'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best',
                'merge_output_format': 'mp4'
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_video.%(ext)s'),
            })

    if progress_hook:
        ydl_opts['progress_hooks'] = [progress_hook]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            if quality == 'thumbnail':
                ident = info.get('id', 'thumb')
                # Try finding the downloaded thumb
                for ext in ['jpg', 'webp', 'png']:
                    path = os.path.join(DOWNLOAD_DIR, f"{ident}.{ext}")
                    if os.path.exists(path):
                        return {"success": True, "filepath": path, "size": os.path.getsize(path), "title": "Cover"}
                return {"success": False, "error": "Thumbnail not found"}
                
            filename = ydl.prepare_filename(info)
            if quality == 'mp3':
                # FFmpeg extracts to .mp3, prepare_filename might have .webm, replace it
                filename = os.path.splitext(filename)[0] + '.mp3'
            elif info.get('ext') != 'mp4':
                 if not os.path.exists(filename) and os.path.exists(os.path.splitext(filename)[0] + '.mp4'):
                     filename = os.path.splitext(filename)[0] + '.mp4'
            
            size = os.path.getsize(filename) if os.path.exists(filename) else 0
            return {
                "success": True,
                "filepath": filename,
                "size": size,
                "title": info.get('title', 'Video')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
