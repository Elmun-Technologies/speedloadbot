from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.translations import TEXTS

def get_language_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_youtube_keyboard(lang: str, sizes: dict = None):
    texts = TEXTS.get(lang, TEXTS["uz"])
    def f_btn(q):
        size = sizes.get(q) if sizes else None
        label = f"🎬 {q}" if q != 'mp3' else texts["quality_audio"]
        if size:
            label += f" • {size}MB"
        return InlineKeyboardButton(label, callback_data=f"quality_{q}")

    keyboard = [
        [f_btn('360p'), f_btn('720p'), f_btn('1080p')],
        [f_btn('mp3')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_instagram_keyboard(lang: str):
    texts = TEXTS.get(lang, TEXTS["uz"])
    keyboard = [
        [
            InlineKeyboardButton(f"🎬 {texts['btn_download']}", callback_data="quality_best"),
            InlineKeyboardButton(texts["quality_audio"], callback_data="quality_mp3")
        ],
        [
            InlineKeyboardButton(texts["quality_thumbnail"], callback_data="quality_thumbnail")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_universal_keyboard(lang: str, sizes: dict = None):
    texts = TEXTS.get(lang, TEXTS["uz"])
    def f_btn(q):
        size = sizes.get(q) if (sizes and q == 'best') else (sizes.get('mp3') if (sizes and q == 'mp3') else None)
        label = f"🎬 {texts['btn_download']}" if q == 'best' else texts["quality_audio"]
        if size:
            label += f" • {size}MB"
        return InlineKeyboardButton(label, callback_data=f"quality_{q}")

    keyboard = [
        [f_btn('best'), f_btn('mp3')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_platforms_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("YouTube", callback_data="plat_YouTube"),
            InlineKeyboardButton("Instagram", callback_data="plat_Instagram")
        ],
        [
            InlineKeyboardButton("TikTok", callback_data="plat_TikTok"),
            InlineKeyboardButton("Twitter / X", callback_data="plat_Twitter")
        ],
        [
            InlineKeyboardButton("Facebook", callback_data="plat_Facebook"),
            InlineKeyboardButton("Pinterest", callback_data="plat_Pinterest")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
def get_help_keyboard(lang: str):
    texts = TEXTS.get(lang, TEXTS["uz"])
    keyboard = [
        [InlineKeyboardButton(texts["btn_tickets"], callback_data="help_tickets")],
        [InlineKeyboardButton(texts["btn_support"], url="https://t.me/speedload_support")]
    ]
    return InlineKeyboardMarkup(keyboard)
