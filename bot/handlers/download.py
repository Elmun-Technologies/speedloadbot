import time
import random
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import get_user, create_download, get_limits, update_user_engagement
from utils.translations import TEXTS
from utils.human_touch import send_typing, detect_video_type, get_random_reaction
from utils.file_sizes import get_format_sizes
from downloader.detector import detect_platform
from downloader.youtube import extract_youtube_info
from downloader.instagram import extract_instagram_info
from downloader.universal import extract_universal_info
from bot.keyboards.inline import get_youtube_keyboard, get_instagram_keyboard, get_universal_keyboard, get_platforms_keyboard
from tasks.download_task import process_download
from datetime import timedelta, datetime
import asyncio
from utils.human_touch import (
    send_typing, detect_video_type, get_random_reaction, 
    check_content_filter, get_nudge_message, get_quote
)
from utils.integration import process_user_action
from utils.streak_system import format_leaderboard

def format_duration(seconds):
    if not seconds: return "0:00"
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        if not db_user:
            return
        lang = db_user.language
        texts = TEXTS.get(lang, TEXTS["uz"])
        
    # Main menu button intercepts
    if text in [TEXTS["uz"]["btn_account"], TEXTS["ru"]["btn_account"], TEXTS["en"]["btn_account"]]:
        from bot.handlers.account import account_handler
        return await account_handler(update, context)
        
    if text in [TEXTS["uz"]["btn_download"], TEXTS["ru"]["btn_download"], TEXTS["en"]["btn_download"]]:
        await send_typing(context, chat_id)
        await update.message.reply_text(texts["choose_platform"], reply_markup=get_platforms_keyboard())
        return
        
    if text in [TEXTS["uz"]["btn_referral"], TEXTS["ru"]["btn_referral"], TEXTS["en"]["btn_referral"]]:
        from bot.handlers.referral import referral_handler
        return await referral_handler(update, context)
        
    if text in [TEXTS["uz"]["btn_language"], TEXTS["ru"]["btn_language"], TEXTS["en"]["btn_language"]]:
        from bot.handlers.language import language_command
        return await language_command(update, context)
        
    if text in [TEXTS["uz"]["btn_language"], TEXTS["ru"]["btn_language"], TEXTS["en"]["btn_language"]]:
        from bot.handlers.language import language_command
        return await language_command(update, context)

    if text in [TEXTS["uz"]["btn_creators"], TEXTS["ru"]["btn_creators"], TEXTS["en"]["btn_creators"]]:
        from bot.handlers.creators import creators_handler
        return await creators_handler(update, context)

    if text in ["🏆 Reyting", "🏆 Рейтинг", "🏆 Leaderboard"]:
        return await leaderboard_handler(update, context)

    if not text or not (text.startswith("http") or text.startswith("www")):
        return

    # Human Touch: Content Filter
    filter_res = check_content_filter(text, lang)
    if filter_res['triggered']:
        await update.message.reply_text(filter_res['message'], disable_web_page_preview=False)
        return

    # Engagement Tracking (Gamification)
    await process_user_action(user.id, 'download', context.bot, lang)

    platform = detect_platform(text)
    if platform == "other":
        await update.message.reply_text(texts["unsupported"])
        return

    msg = await update.message.reply_text(random.choice(texts["loading"]))
    
    info = None
    sizes = {}
    if platform == "youtube":
        info = extract_youtube_info(text)
        if info:
            sizes = get_format_sizes(text)
            keyboard = get_youtube_keyboard(lang, sizes)
    elif platform == "instagram":
        info = extract_instagram_info(text)
        if info:
            keyboard = get_instagram_keyboard(lang)
    else:
        info = extract_universal_info(text)
        if info:
            sizes = get_format_sizes(text)
            keyboard = get_universal_keyboard(lang, sizes)

    if not info:
        await msg.edit_text(texts["private"])
        return

    # Human Touch: Context React
    v_type = detect_video_type(info.get('title', ''), info.get('uploader', ''))
    reaction = get_random_reaction(v_type)
    
    caption = ""
    if platform == "youtube":
        caption = f"{reaction}\n\n🎬 **{info.get('title')}**\n👤 Kanal: {info.get('uploader')}\n⏱ Davomiyligi: {format_duration(info.get('duration'))}\n👁 {info.get('view_count'):,} ko'rishlar\n\n📦 **Sifat tanlang:**"
    elif platform == "instagram":
        caption = f"{reaction}\n\n📸 @{info.get('uploader')}\n📝 {info.get('description')}\n👁 {info.get('view_count'):,} ko'rishlar ❤️ {info.get('like_count'):,} like\n\n{texts['what_to_download']}"
    else:
        caption = f"{reaction}\n\n🎬 **{info.get('title', 'Video')}**\n⏱ Davomiyligi: {format_duration(info.get('duration', 0))}\n\n📦 **Sifat tanlang:**"

    message_id = update.message.message_id
    context.user_data[f"url_{message_id}"] = text
    context.user_data[f"platform_{message_id}"] = platform
    context.user_data[f"title_{message_id}"] = info.get("title", "Video")
    context.user_data[f"duration_{message_id}"] = info.get("duration", 0)

    # Human Touch: Nudge (Small delay for realism)
    nudge = get_nudge_message('download', user.first_name, lang)
    if nudge:
        async def send_delayed_nudge():
            await asyncio.sleep(2)
            await context.bot.send_message(chat_id=chat_id, text=nudge)
        asyncio.create_task(send_delayed_nudge())


async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    quality = data.split("_")[1]
    
    original_msg_id = query.message.reply_to_message.message_id if query.message.reply_to_message else None
    url = context.user_data.get(f"url_{original_msg_id}")
    platform = context.user_data.get(f"platform_{original_msg_id}", "other")
    title = context.user_data.get(f"title_{original_msg_id}", "Video")
    duration = context.user_data.get(f"duration_{original_msg_id}", 0)

    if not url:
        return

    user = update.effective_user
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        if not db_user:
            return
            
        lang = db_user.language
        texts = TEXTS.get(lang, TEXTS["uz"])
        
        # Credits deductor skipped as per user's "no limit" rule in previous turn
        # but let's keep the download record
        from database.crud import create_download as db_create_download
        dl = await db_create_download(session, db_user.id, url, platform, quality, title, duration)
        download_id = dl.id

    loading_msgs = texts["loading"]
    fun_msg = random.choice(loading_msgs)
    
    if query.message.caption:
        await query.edit_message_caption(caption=fun_msg)
    else:
        await query.edit_message_text(text=fun_msg)
    
    process_download.delay(
        telegram_id=user.id,
        chat_id=query.message.chat_id,
        message_id=query.message.id, # Fixed typo from previous version
        url=url,
        quality=quality,
        download_id=download_id,
        language=lang,
        has_caption=bool(query.message.caption)
    )

async def platform_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")[1]
    
    user = update.effective_user
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        if not db_user:
            return
        lang = db_user.language
        texts = TEXTS.get(lang, TEXTS["uz"])
        
    await query.message.reply_text(texts["send_link_prompt"].format(platform=data))
async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database.crud import get_top_users_by_downloads
    user = update.effective_user
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        lang = db_user.language if db_user else 'uz'
        top_users = await get_top_users_by_downloads(session, limit=10)
        
    text = format_leaderboard(top_users, lang)
    await update.message.reply_text(text)
