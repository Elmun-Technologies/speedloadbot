import yt_dlp

def get_format_sizes(url: str) -> dict:
    """
    Extracts available formats and their estimated sizes from yt-dlp.
    Returns: { '360p': 12.5, '720p': 45.0, ... } (Sizes in MB)
    """
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    
    sizes = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # Find best sizes for 360, 720, 1080 and mp3
            # Simple heuristic: pick the first one matching height
            for f in formats:
                h = f.get('height')
                size = f.get('filesize') or f.get('filesize_approx', 0)
                if not size:
                    continue
                
                size_mb = round(size / (1024 * 1024), 1)
                
                if h == 360 and '360p' not in sizes:
                    sizes['360p'] = size_mb
                elif h == 720 and '720p' not in sizes:
                    sizes['720p'] = size_mb
                elif h == 1080 and '1080p' not in sizes:
                    sizes['1080p'] = size_mb
                elif f.get('ext') in ['mp3', 'm4a', 'webm'] and f.get('vcodec') == 'none':
                    # Best audio size
                    current_aud = sizes.get('mp3', 0)
                    if size_mb > current_aud:
                        sizes['mp3'] = size_mb
            
            return sizes
        except Exception:
            return {}
