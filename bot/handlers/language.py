from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import update_user_language, get_user
from bot.keyboards.inline import get_language_keyboard
from utils.translations import TEXTS
from bot.keyboards.reply import get_main_menu

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        lang = db_user.language if db_user else "uz"
        
    texts = TEXTS.get(lang, TEXTS["uz"])
    # "Select language" prompt
    prompt = "Iltimos, tilni tanlang:" if lang == "uz" else ("Пожалуйста, выберите язык:" if lang == "ru" else "Please select a language:")
    await update.message.reply_text(prompt, reply_markup=get_language_keyboard())

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split("_")[1] # lang_uz -> uz
    
    async with AsyncSessionLocal() as session:
        await update_user_language(session, update.effective_user.id, lang)
        
    from utils.human_touch import send_typing
    await send_typing(context, query.message.chat_id, 0.4)
    await query.message.reply_text(texts["language_updated"], reply_markup=get_main_menu(lang))
    await query.delete_message()
