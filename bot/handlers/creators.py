import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import get_user
from utils.translations import TEXTS
from utils.human_touch import send_typing
from bot.keyboards.creators import get_creators_menu
from bot.keyboards.reply import get_main_menu
from config import DOWNLOAD_DIR
from database.crud import update_user_profile
from utils.integration import process_user_action
from bot.handlers.trends import trend_radar_handler

async def creators_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await send_typing(context, chat_id, 0.5)
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        lang = db_user.language if db_user else "uz"
        credits = db_user.creator_credits if db_user else 0
        
    texts = TEXTS.get(lang, TEXTS["uz"])
    keyboard = get_creators_menu(lang)
    
    title = texts["creator_title"]
    credits_info = texts["creator_credits_info"].format(credits=credits)
    
    await update.message.reply_text(f"{title}\n\n{credits_info}", reply_markup=keyboard, parse_mode="Markdown")

async def creator_tool_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        lang = db_user.language if db_user else "uz"
        credits = db_user.creator_credits if db_user else 0
        is_premium = db_user.is_premium if db_user else False
        
    texts = TEXTS.get(lang, TEXTS["uz"])
    
    if text == texts["btn_back"]:
        from bot.keyboards.reply import get_main_menu
        await update.message.reply_text(texts["status_main_menu"], reply_markup=get_main_menu(lang))
        return True

    if text == texts["btn_buy_credits"]:
        from database.crud import get_referral_stats
        async with AsyncSessionLocal() as session:
             ref_count, _ = await get_referral_stats(session, user.id)
        
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user.id}"
        
        msg_text = (
            "💳 **Kredit sotib olish / Upgrade**\n\n"
            "Tez orada bu bo'limda Payme va Click orqali to'lov ulanadi! 🚀\n\n"
            "Hozircha **BEPUL** kredit olishingiz mumkin! Shunchaki do'stlaringizni taklif qiling:\n"
            "✅ Har bir taklif qilingan do'st uchun **+3 ta Creator krediti** beriladi.\n\n"
            f"🔗 Sizning referal havolangiz:\n`{ref_link}`\n\n"
            f"👥 Siz taklif qilgan do'stlar: {ref_count} kishi"
        )
        await update.message.reply_text(msg_text, parse_mode="Markdown")
        return True

    # Check which tool was clicked
    tool_map = {
        texts["btn_v2script"]: "v2script",
        texts["btn_cleanmeta"]: "cleanmeta",
        texts["btn_compress"]: "compress",
        texts["btn_thumbnail"]: "thumbnail",
        texts["btn_trendradar"]: "trendradar",
        texts["btn_longtoshort"]: "longtoshort"
    }
    
    tool = tool_map.get(text)
    if not tool:
        return False 
        
    # Credit Check
    if not is_premium and credits <= 0:
        await update.message.reply_text(texts["no_credits_error"], parse_mode="Markdown")
        return True

    context.user_data["active_tool"] = tool
    
    if tool == "trendradar":
        return await trend_radar_handler(update, context)
        
    description = texts["tool_descriptions"].get(tool, texts["status_send_file"])
    await send_typing(context, chat_id, 0.4)
    await update.message.reply_text(description, parse_mode="Markdown")
    return True


async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tool = context.user_data.get("active_tool")
    if not tool:
        return # Not in creator flow
        
    user = update.effective_user
    chat_id = update.effective_chat.id
    msg = update.message
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        lang = db_user.language if db_user else "uz"
    texts = TEXTS.get(lang, TEXTS["uz"])
    
    # Download the file
    file = None
    if msg.video: file = msg.video
    elif msg.audio: file = msg.audio
    elif msg.document: file = msg.document
    elif msg.photo: file = msg.photo[-1]
    
    if not file and tool != "thumbnail":
        await msg.reply_text(texts["status_send_file"])
        return

    # Deduct credit before processing (or after success? Let's do before to be safe against long tasks)
    async with AsyncSessionLocal() as session:
        from database.crud import update_user_profile
        db_user = await get_user(session, user.id)
        if not db_user.is_premium:
            await update_user_profile(session, db_user.id, creator_credits=db_user.creator_credits - 1)

    status_msg = await msg.reply_text(texts["status_processing"])
    await context.bot.send_chat_action(chat_id, "upload_document")

    # Download logic
    file_id = file.file_id if file else "link_tool"
    if file:
        new_file = await context.bot.get_file(file_id)
        ext = os.path.splitext(new_file.file_path)[1]
        input_path = os.path.join(DOWNLOAD_DIR, f"{file_id}{ext}")
        await new_file.download_to_drive(input_path)
    else:
        input_path = None

    try:
        if tool == "cleanmeta" and input_path:
            from utils.ffmpeg_tools import strip_metadata
            output_path = os.path.join(DOWNLOAD_DIR, f"clean_{file_id}{ext}")
            if strip_metadata(input_path, output_path):
                with open(output_path, 'rb') as f:
                    await msg.reply_document(f, caption=texts["status_done"])
            else:
                await msg.reply_text(texts["status_error"])
                
        elif tool == "compress" and input_path:
            from utils.ffmpeg_tools import compress_video
            output_path = os.path.join(DOWNLOAD_DIR, f"comp_{file_id}.mp4")
            await status_msg.edit_text(texts["status_compressing"])
            if compress_video(input_path, output_path):
                size_before = round(os.path.getsize(input_path)/1024/1024, 1)
                size_after = round(os.path.getsize(output_path)/1024/1024, 1)
                with open(output_path, 'rb') as f:
                    await msg.reply_video(f, caption=f"✅ {size_before}MB → {size_after}MB")
            else:
                await msg.reply_text(texts["status_error"])

        elif tool == "v2script" and (input_path or msg.text):
            from utils.transcriber import transcribe_video
            await status_msg.edit_text(texts["status_transcribing"])
            
            # transcription logic
            source = input_path if input_path else (msg.text if msg.text and "http" in msg.text else None)
            if not source:
                 await msg.reply_text(texts["status_send_file"])
                 return

            script_text = await asyncio.to_thread(transcribe_video, source)
            
            txt_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(script_text)
            
            if len(script_text) > 4000:
                await msg.reply_text(texts["status_too_long"])
            else:
                await msg.reply_text(f"📝 **Script:**\n\n{script_text}", parse_mode="Markdown")
                
            with open(txt_path, "rb") as f:
                await msg.reply_document(f, filename="script.txt")

        elif tool == "thumbnail":
            # Thumbnail doesn't need a file, it needs a link
            url = msg.text if msg.text and "http" in msg.text else None
            if not url:
                await msg.reply_text(texts["status_send_file"])
                return
            
            from downloader.youtube import extract_youtube_info
            info = extract_youtube_info(url)
            if info and info.get("thumbnail"):
                await msg.reply_photo(photo=info["thumbnail"], caption=texts["status_done"])
            else:
                await msg.reply_text("❌ Thumbnail topilmadi.")

        elif tool == "longtoshort" and input_path:
            await status_msg.edit_text("🎞 Long to Short: AI tahlil boshlandi... Eng yaxshi momentlarni qidiryapman.")
            from utils.aicut import smart_cut_shorts
            shorts_paths = smart_cut_shorts(input_path, DOWNLOAD_DIR)
            
            for i, s_path in enumerate(shorts_paths):
                with open(s_path, 'rb') as f:
                    await msg.reply_video(f, caption=f"🔥 AI Shorts #{i+1}")
                os.remove(s_path)
            
            if not shorts_paths:
                await msg.reply_text("❌ Video tahlilida muammo bo'ldi yoki video juda qisqa.")

    finally:
        # Cleanup
        if input_path and os.path.exists(input_path): os.remove(input_path)
        context.user_data["active_tool"] = None
        
        # Engagement Tracking (Gamification)
        await process_user_action(user.id, 'creator_use', context.bot, lang)

        await status_msg.delete()
