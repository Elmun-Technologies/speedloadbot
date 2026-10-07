from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import get_user


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        if not db_user:
            return

        credits = db_user.credits or 0
        total_downloads = db_user.total_downloads or 0
        date_str = db_user.created_at.strftime("%Y-%m-%d") if db_user.created_at else "-"

        text = (
            "💰 Hisobingiz\n"
            f"💎 Kredit: {credits} ta\n"
            f"📥 Yuklab olingan: {total_downloads} ta video\n"
            f"📅 A'zo bo'lgan sana: {date_str}"
        )
        await update.message.reply_text(text)
