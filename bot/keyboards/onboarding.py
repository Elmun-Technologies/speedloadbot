from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.translations import TEXTS

def get_interests_keyboard(lang: str):
    texts = TEXTS.get(lang, TEXTS["uz"])
    keyboard = [
        [
            InlineKeyboardButton(texts["interest_ent"], callback_data="interest_entertainment"),
            InlineKeyboardButton(texts["interest_biz"], callback_data="interest_business")
        ],
        [
            InlineKeyboardButton(texts["interest_edu"], callback_data="interest_education"),
            InlineKeyboardButton(texts["interest_tech"], callback_data="interest_technology")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_occupation_keyboard(lang: str):
    texts = TEXTS.get(lang, TEXTS["uz"])
    keyboard = [
        [
            InlineKeyboardButton(texts["occ_creator"], callback_data="occ_creator"),
            InlineKeyboardButton(texts["occ_student"], callback_data="occ_student")
        ],
        [
            InlineKeyboardButton(texts["occ_pro"], callback_data="occ_professional"),
            InlineKeyboardButton(texts["occ_other"], callback_data="occ_other")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
