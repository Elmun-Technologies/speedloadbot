import yt_dlp

def extract_instagram_info(url: str):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                "uploader": info.get("uploader", "Unknown"),
                "description": info.get("description", "")[:200] + ("..." if len(info.get("description", "")) > 200 else ""),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "thumbnail": info.get("thumbnail")
            }
        except Exception:
            return None
