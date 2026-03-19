import asyncio
import json
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import (
    get_user, get_active_trends, log_trend_view, 
    add_trend, deactivate_old_trends
)
from utils.trends import (
    format_trend_card, format_trend_radar_intro, 
    format_trend_radar_outro, get_week_label, research_weekly_trends
)
from utils.integration import process_user_action
from config import OPENAI_API_KEY
import openai

# OpenAI Client
client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

ADMIN_IDS = [6241083439] # Update as needed

async def trend_radar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler when user taps Trend Radar button"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        lang = db_user.language if db_user else 'uz'
        
        # Get current week
        week = datetime.now().strftime('%Y-W%W')
        week_label = get_week_label(lang)
        
        # Get active trends
        trends = await get_active_trends(session, week, lang)
        if not trends:
            trends = await get_active_trends(session, None, lang)
            
        if not trends:
            no_trends = {
                'uz': "🔄 Trend Radar yangilanmoqda...\n\nHar dushanba yangi trendlar qo'shiladi!\n🔔 Dushanba kuni qayta kiring.",
                'ru': "🔄 Trend Radar обновляется...\n\nКаждый понедельник новые тренды!\n🔔 Заходите в понедельник.",
            }
            return await update.message.reply_text(no_trends.get(lang, no_trends['uz']))

        # Track view
        await log_trend_view(session, user.id)
        await process_user_action(user.id, 'trend_view', context.bot, lang)
        
        # Send intro
        intro = format_trend_radar_intro(week_label, lang)
        await update.message.reply_text(intro)
        await asyncio.sleep(1.5)
        
        # Send trends
        for i, trend in enumerate(trends, 1):
            # Convert SQLAlchemy object to dict for formatter if needed
            trend_dict = {c.name: getattr(trend, c.name) for c in trend.__table__.columns}
            card = format_trend_card(trend_dict, i, len(trends), lang)
            
            await update.message.reply_text(card, disable_web_page_preview=False)
            await log_trend_view(session, user.id, trend.id)
            
            if i < len(trends):
                await asyncio.sleep(2.0)
                
        # Send outro
        await asyncio.sleep(1.5)
        outro = format_trend_radar_outro(len(trends), lang)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="🔁 Yana ko'rish" if lang == 'uz' else "🔁 Посмотреть снова", 
                    callback_data="trend_radar_again"
                ),
                InlineKeyboardButton(
                    text="💡 Menga mos trend" if lang == 'uz' else "💡 Подходящий тренд", 
                    callback_data="trend_personalized"
                )
            ]
        ])
        
        await update.message.reply_text(outro, reply_markup=keyboard)

async def handle_trend_personalized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user_id)
        lang = db_user.language if db_user else 'uz'
        user_industry = db_user.interests or 'general'
        
        trends = await get_active_trends(session, None, lang)
        if not trends:
            return await query.message.reply_text("Hozircha trend yo'q!")

        trends_summary = '\n'.join([
            f"- {t.title}: {t.description}" for t in trends
        ])

        prompt = f"""Foydalanuvchi haqida:
- Soha: {user_industry}
- Til: {lang}

Mavjud trendlar:
{trends_summary}

Bu foydalanuvchi uchun eng mos 1 ta trendni tanlang bo'yicha tavsiya bering.
Faqat trend nomini va nima uchun mos ekanini 1-2 jumlada yozing."""

        response = await client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=200,
        )
        
        ai_suggestion = response.choices[0].message.content
        
        msgs = {
            'uz': f"🤖 AI tavsiyasi:\n\n{ai_suggestion}\n\n✨ Bu trend siz uchun eng mos!",
            'ru': f"🤖 Совет от AI:\n\n{ai_suggestion}\n\n✨ Этот тренд подходит вам больше всего!",
        }
        
        await query.message.reply_text(msgs.get(lang, msgs['uz']))

# === ADMIN COMMANDS ===

async def cmd_update_trends_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
        
    await update.message.reply_text("🔄 AI trendlarni izlayapti...")
    
    week = datetime.now().strftime('%Y-W%W')
    
    try:
        new_trends = await research_weekly_trends(client, week)
        
        async with AsyncSessionLocal() as session:
            # Deactivate old
            await deactivate_old_trends(session, week)
            
            added = 0
            for trend_data in new_trends:
                await add_trend(session, {**trend_data, 'week_number': week, 'is_active': True})
                added += 1
                
        await update.message.reply_text(f"✅ {added} ta yangi trend qo'shildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")
