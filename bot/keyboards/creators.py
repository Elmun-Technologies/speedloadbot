from telegram import ReplyKeyboardMarkup, KeyboardButton
from utils.translations import TEXTS

def get_creators_menu(lang: str):
    texts = TEXTS.get(lang, TEXTS["uz"])
    keyboard = [
        [KeyboardButton(texts["btn_v2script"]), KeyboardButton(texts["btn_cleanmeta"])],
        [KeyboardButton(texts["btn_compress"]), KeyboardButton(texts["btn_thumbnail"])],
        [KeyboardButton(texts["btn_trendradar"]), KeyboardButton(texts["btn_longtoshort"])],
        [KeyboardButton(texts["btn_buy_credits"]), KeyboardButton(texts["btn_back"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
