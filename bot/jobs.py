import asyncio
import random
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.models import User
from sqlalchemy import select

from datetime import datetime, timedelta
import pytz

async def get_active_users():
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.last_active >= seven_days_ago)
        result = await session.execute(stmt)
        return result.scalars().all()

async def morning_motivation_job(context: ContextTypes.DEFAULT_TYPE):
    from utils.human_touch import get_morning_message
    users = await get_active_users()
    
    for user in users:
        msg = get_morning_message(user.language)
        try:
            await context.bot.send_message(chat_id=user.telegram_id, text=msg)
            await asyncio.sleep(0.05)
        except Exception:
            pass

async def juma_greeting_job(context: ContextTypes.DEFAULT_TYPE):
    from utils.human_touch import get_smart_greeting
    users = await get_active_users()
    
    # We use get_smart_greeting because it already handles Juma logic
    for user in users:
        if user.language == "uz": # Only for UZ users usually, but let's be safe
            msg = get_smart_greeting(user.first_name, user.telegram_id)
            if "Juma" in msg:
                try:
                    await context.bot.send_message(chat_id=user.telegram_id, text=msg)
                    await asyncio.sleep(0.05)
                except Exception:
                    pass

async def weekly_challenge_job(context: ContextTypes.DEFAULT_TYPE):
    from utils.human_touch import get_weekly_challenge
    users = await get_active_users()
    
    for user in users:
        msg = get_weekly_challenge(user.language)
        try:
            await context.bot.send_message(chat_id=user.telegram_id, text=msg)
            await asyncio.sleep(0.05)
        except Exception:
            pass

async def weekly_trend_refresh(context: ContextTypes.DEFAULT_TYPE):
    """Runs every Monday 08:00 — refreshes trends and notifies users"""
    from utils.trends import research_weekly_trends
    from database.crud import deactivate_old_trends, add_trend, get_active_users_for_notification
    from database.connection import AsyncSessionLocal
    import openai
    from config import OPENAI_API_KEY
    
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    week = datetime.now().strftime('%Y-W%W')
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. AI Research
            new_trends = await research_weekly_trends(client, week)
            # 2. Deactivate old
            await deactivate_old_trends(session, week)
            # 3. Save new
            for trend in new_trends:
                await add_trend(session, {**trend, 'week_number': week, 'is_active': True})
            
            # 4. Get active users for notification
            users = await get_active_users_for_notification(session, days=7)
        except Exception as e:
            print(f"Error in weekly_trend_refresh: {e}")
            return
            
    notify_msgs = {
        'uz': "🔥 Bu hafta yangi TRENDLAR tayyor!\n\n📱 Trend Radar ni bosing va viral bo'lishni boshlang!\n\n5 ta yangi trend — real raqamlar bilan! 👇",
        'ru': "🔥 Новые ТРЕНДЫ этой недели готовы!\n\n📱 Нажмите Trend Radar и начните создавать вирусный контент!\n\n5 новых трендов с реальными цифрами! 👇",
    }
    
    for user in users:
        lang = user.language or 'uz'
        msg = notify_msgs.get(lang, notify_msgs['uz'])
        try:
            await context.bot.send_message(chat_id=user.telegram_id, text=msg)
            await asyncio.sleep(0.05)
        except Exception:
            pass
