from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from database.connection import AsyncSessionLocal
from database.crud import get_user, update_user_profile
from utils.translations import TEXTS
from bot.keyboards.onboarding import get_interests_keyboard, get_occupation_keyboard
from bot.keyboards.reply import get_main_menu
from bot.keyboards.inline import get_language_keyboard
import asyncio

# States
SELECT_LANG, SELECT_INTERESTS, SELECT_OCCUPATION = range(3)

async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This is called for NEW users from start_handler or when forcing onboarding
    user = update.effective_user
    # 1. Ask Language
    prompt = "Iltimos, tilni tanlang / Пожалуйста, выберите язык / Please select a language:"
    await update.message.reply_text(prompt, reply_markup=get_language_keyboard())
    return SELECT_LANG

async def onboarding_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split("_")[1]
    user_id = update.effective_user.id
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user_id)
        if db_user:
            await update_user_profile(session, db_user.id, language=lang)
        
    texts = TEXTS.get(lang, TEXTS["uz"])
    # Delete old message and send new one to trigger ReplyKeyboardMarkup update
    await query.message.delete()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=texts["onboarding_interests"],
        reply_markup=get_interests_keyboard(lang),
        parse_mode="Markdown"
    )
    # We also send a dummy message or use the main menu later? 
    # Actually, the best way to update the BOTTOM keyboard is to send get_main_menu(lang).
    # Since we can't have both keyboards in one message, we send the interest inline keyboard 
    # and then in the NEXT step we'll update the main menu. 
    # OR we send a small confirmation now.
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🌐 " + texts["language_updated"] if "language_updated" in texts else "🌐",
        reply_markup=get_main_menu(lang)
    )
    
    return SELECT_INTERESTS

async def onboarding_interest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    interest = query.data.split("_")[1]
    
    # Store in user_data temporarily or update DB
    context.user_data["onb_interest"] = interest
    
    lang = context.user_data.get("lang", "uz") # fallback
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, update.effective_user.id)
        lang = db_user.language
        
    texts = TEXTS.get(lang, TEXTS["uz"])
    await query.message.edit_text(texts["onboarding_occupation"], reply_markup=get_occupation_keyboard(lang))
    return SELECT_OCCUPATION

async def onboarding_occupation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    occ = query.data.split("_")[1]
    interest = context.user_data.get("onb_interest")
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, update.effective_user.id)
        if db_user:
            await update_user_profile(
                session, 
                db_user.id, 
                interests=interest, 
                occupation=occ, 
                onboarding_completed=True
            )
        lang = db_user.language
        
    texts = TEXTS.get(lang, TEXTS["uz"])
    
    from utils.human_touch import send_typing
    await send_typing(context, query.message.chat_id, 0.5)
    await query.message.reply_text(
        texts["welcome_new"], 
        reply_markup=get_main_menu(lang),
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END

async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Fallback to main menu if they cancel? 
    # But we want to force it for data. Let's just end it.
    return ConversationHandler.END

from bot.handlers.start import start_handler

# ...

onboarding_conv = ConversationHandler(
    entry_points=[CommandHandler("start", start_handler)],
    states={
        SELECT_LANG: [CallbackQueryHandler(onboarding_lang_callback, pattern="^lang_")],
        SELECT_INTERESTS: [CallbackQueryHandler(onboarding_interest_callback, pattern="^interest_")],
        SELECT_OCCUPATION: [CallbackQueryHandler(onboarding_occupation_callback, pattern="^occ_")],
    },
    fallbacks=[CommandHandler("start", start_handler)], # Allow restart
    allow_reentry=True
)

