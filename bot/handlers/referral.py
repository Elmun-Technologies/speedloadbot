from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import get_user, get_referral_stats
from utils.translations import TEXTS

async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        if not db_user:
            return
            
        count, earned = await get_referral_stats(session, db_user.id)
        bot_me = await context.bot.get_me()
        bot_username = bot_me.username
        
        lang = db_user.language
        texts = TEXTS.get(lang, TEXTS["uz"])
        
        link = f"https://t.me/{bot_username}?start=ref_{db_user.referral_code}"
        
        text = texts["referral"].format(
            link=link,
            count=count
        )
        await update.message.reply_text(text)
