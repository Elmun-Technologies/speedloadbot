from telegram import ReplyKeyboardMarkup, KeyboardButton
from utils.translations import TEXTS

def get_main_menu(lang: str):
    texts = TEXTS.get(lang, TEXTS["uz"])
    keyboard = [
        [KeyboardButton(texts["btn_download"])],
        [KeyboardButton(texts["btn_creators"])],
        [KeyboardButton(texts["btn_account"]), KeyboardButton(texts["btn_referral"])],
        [KeyboardButton(texts["btn_leaderboard"])],
        [KeyboardButton(texts["btn_language"]), KeyboardButton(texts["btn_help"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
