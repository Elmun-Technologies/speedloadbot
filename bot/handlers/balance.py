from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import get_user, get_user_stats

async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        if not db_user:
            return
            
        total_downloads = await get_user_stats(session, db_user.id)
        
        date_str = db_user.created_at.strftime("%Y-%m-%d")
        
        text = (
            "💰 Sizning hisobingiz\n"
            f"Coin: {db_user.coins} ta\n"
            f"Yuklab olingan: {total_downloads} ta video\n"
            f"A'zo bo'lgan: {date_str}"
        )
        await update.message.reply_text(text)
