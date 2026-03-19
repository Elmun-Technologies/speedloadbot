import re

PLATFORMS = {
    "youtube": re.compile(r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]+)"),
    "instagram": re.compile(r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)"),
    "tiktok": re.compile(r"(?:https?:\/\/)?(?:www\.)?(?:tiktok\.com|vt\.tiktok\.com)\/.*"),
    "twitter": re.compile(r"(?:https?:\/\/)?(?:www\.)?(?:twitter\.com|x\.com)\/.*\/status\/[0-9]+"),
    "facebook": re.compile(r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/.*"),
    "pinterest": re.compile(r"(?:https?:\/\/)?(?:www\.)?pinterest\.com\/pin\/.*")
}

def detect_platform(url: str) -> str:
    for name, pattern in PLATFORMS.items():
        if pattern.search(url):
            return name
    return "other"
