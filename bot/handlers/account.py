```python
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import get_user, get_limits, get_referral_stats
from utils.translations import TEXTS
from utils.human_touch import send_typing
from utils.streak_system import format_full_profile
from datetime import datetime

async def account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await send_typing(context, chat_id, 0.6)
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        if not db_user:
            return
            
        limits = await get_limits(session, user.id)
        ref_count, _ = await get_referral_stats(session, db_user.id)
        lang = db_user.language
        texts = TEXTS.get(lang, TEXTS["uz"])
        
        from utils.human_touch import format_profile
        
        # Prepare data for formatting
        # Convert for formatter
        user_data = {
            'name': db_user.first_name,
            'telegram_id': db_user.telegram_id,
            'created_at': db_user.created_at,
            'total_downloads': db_user.total_downloads,
            'total_creator_uses': db_user.total_creator_uses,
            'total_referrals': ref_count,
            'credits': db_user.credits,
            'streak_days': db_user.streak_days,
            'streak_longest': db_user.streak_longest,
            'total_points': db_user.total_points,
            'level': db_user.level,
            'badges': db_user.badges
        }
        
        text = format_full_profile(user_data, lang)
        
        keyboard = [
            [InlineKeyboardButton(texts["btn_donate"], callback_data="donate_info")]
        ]
        
        await update.message.reply_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="HTML"
        )

async def donate_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user_id)
        lang = db_user.language if db_user else "uz"
        
    texts = TEXTS.get(lang, TEXTS["uz"])
    await query.message.reply_text(texts["donate_text"], parse_mode="Markdown")

