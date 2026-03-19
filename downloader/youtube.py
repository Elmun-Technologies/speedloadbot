import yt_dlp

def extract_youtube_info(url: str):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "YouTube Video"),
                "uploader": info.get("uploader", "Unknown Channel"),
                "duration": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "thumbnail": info.get("thumbnail")
            }
        except Exception:
            return None
