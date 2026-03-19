import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database.connection import AsyncSessionLocal
from database.models import User, Download
from sqlalchemy import select, func
import logging

# ADMIN IDs
ADMINS = [6241083439] # Nazir E.

# Conversation States
BROADCAST_MESSAGE = 1

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return

    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Xabar yuborish (Broadcast)", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📩 Murojaatlar (Tickets)", callback_data="admin_tickets")]
    ]
    
    await update.message.reply_text(
        "🛠 **Admin Panel**\n\nSpeedLoad botini boshqarish va tahlil qilish bo'limi.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await query.answer("Ruxsat yo'q!", show_alert=True)
        return

    await query.answer()
    data = query.data

    if data == "admin_stats":
        async with AsyncSessionLocal() as session:
            # Users
            total_users = await session.scalar(select(func.count(User.id)))
            
            # Downloads
            total_downloads = await session.scalar(select(func.count(Download.id)))
            yt_count = await session.scalar(select(func.count(Download.id)).where(Download.platform == "youtube"))
            ig_count = await session.scalar(select(func.count(Download.id)).where(Download.platform == "instagram"))
            tk_count = await session.scalar(select(func.count(Download.id)).where(Download.platform == "tiktok"))
            other_count = total_downloads - (yt_count + ig_count + tk_count)

        text = (
            "📊 **SPEEDLOAD TRACTION**\n\n"
            f"👥 **Jami foydalanuvchilar**: `{total_users}`\n"
            f"📥 **Jami yuklamalar**: `{total_downloads}`\n\n"
            "━━━━━━━━━━━━━━━\n"
            "📈 **Platformalar bo'yicha**\n"
            "━━━━━━━━━━━━━━━\n"
            f"📹 YouTube: `{yt_count}`\n"
            f"📸 Instagram: `{ig_count}`\n"
            f"🎵 TikTok: `{tk_count}`\n"
            f"🔗 Boshqa: `{other_count}`\n"
        )
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=query.message.reply_markup)

    elif data == "admin_broadcast":
        await query.message.reply_text("📢 **Barcha foydalanuvchilarga xabar yuborish.**\n\nIltimos, xabarni matnini yuboring (yoki rasmli xabar bo'lsa rasmini yuboring):", parse_mode="Markdown")
        return BROADCAST_MESSAGE

    elif data == "admin_tickets":
        # Placeholder for ticket viewing
        await query.message.reply_text("📩 Murojaatlar ro'yxati tez orada bu yerda ko'rinadi. (Phase 8 implementatsiyasi bo'yicha loglarni ko'ring).")

async def broadcast_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    msg = update.message
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()

    sent_count = 0
    fail_count = 0
    
    status_msg = await msg.reply_text(f"🚀 Yuborish boshlandi: 0/{len(users)}")
    
    for i, user in enumerate(users):
        try:
            if msg.photo:
                await context.bot.send_photo(chat_id=user.telegram_id, photo=msg.photo[-1].file_id, caption=msg.caption)
            else:
                await context.bot.send_message(chat_id=user.telegram_id, text=msg.text)
            sent_count += 1
        except Exception:
            fail_count += 1
            
        if i % 10 == 0:
            try:
                await status_msg.edit_text(f"🚀 Yuborish jarayoni: {sent_count}/{len(users)} (Xato: {fail_count})")
            except: pass
        await asyncio.sleep(0.05)

    await msg.reply_text(f"✅ **Yuborish yakunlandi!**\n\nSiz yubordingiz: `{sent_count}`\nXatoliklar: `{fail_count}`", parse_mode="Markdown")
    return ConversationHandler.END

async def cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin jarayoni bekor qilindi.")
    return ConversationHandler.END

admin_broadcast_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_callback_handler, pattern="^admin_broadcast$")],
    states={
        BROADCAST_MESSAGE: [MessageHandler(filters.TEXT | filters.PHOTO, broadcast_message_handler)]
    },
    fallbacks=[CommandHandler("cancel", cancel_admin)],
    per_message=False # Use False for callback entry points usually
)
