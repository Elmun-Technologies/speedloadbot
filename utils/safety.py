import re

BANNED_KEYWORDS = [
    r'porn', r'sex', r'xxx', r'xvideo', r'brazzers', r'hentai', r'erotic',
    r'shaxvat', r'jinsiy', r'yalang\'och', r'порно', r'секс', r'сиськи', r'голая'
]

BANNED_DOMAINS = [
    'pornhub.com', 'xvideos.com', 'xnxx.com', 'redtube.com', 'youporn.com'
]

MORAL_REDIRECT_URL = "https://www.youtube.com/watch?v=DyunCIco-4Y"

def is_safe(text: str) -> bool:
    if not text:
        return True
    
    # Check domains
    for domain in BANNED_DOMAINS:
        if domain in text.lower():
            return False
            
    # Check keywords
    for pattern in BANNED_KEYWORDS:
        if re.search(pattern, text.lower(), re.IGNORECASE):
            return False
            
    return True
