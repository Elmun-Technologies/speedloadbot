import os
import time
import asyncio
import requests
import random
from celery import Celery
from telegram import Bot
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, BOT_TOKEN
from downloader.universal import download_media
from database.crud import update_download_status
from utils.translations import TEXTS
from utils.loading_messages import LOADING_MESSAGES

celery_app = Celery("speedload_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery_app.task(bind=True)
def process_download(self, telegram_id, chat_id, message_id, url, quality, download_id, language="uz", has_caption=True):
    last_update = time.time()
    last_fun_update = time.time()
    loading_msgs = LOADING_MESSAGES.get(language, LOADING_MESSAGES["uz"])
    current_fun = random.choice(loading_msgs)

    def progress_hook(d):
        nonlocal last_update, last_fun_update, current_fun
        if d['status'] == 'downloading':
            now = time.time()
            if now - last_fun_update >= 8.0:
                current_fun = random.choice(loading_msgs)
                last_fun_update = now
                
            if now - last_update >= 3.0:
                last_update = now
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                if total:
                    percent = (downloaded / total) * 100
                    text = f"{current_fun}\n\n⏳ {percent:.1f}%"
                    payload = {"chat_id": chat_id, "message_id": message_id}
                    if has_caption:
                        payload["caption"] = text
                        endpoint = "editMessageCaption"
                    else:
                        payload["text"] = text
                        endpoint = "editMessageText"
                    try:
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}", json=payload, timeout=5)
                    except Exception:
                        pass
                        
    result = download_media(url, quality, platform="auto", progress_hook=progress_hook)
    
    async def finalize():
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from config import DATABASE_URL
        from sqlalchemy.pool import NullPool
        
        local_engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
        LocalSession = async_sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)
        bot = Bot(token=BOT_TOKEN)
        texts = TEXTS.get(language, TEXTS["uz"])
        
        async def edit_final_error(msg):
            try:
                if has_caption:
                    await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=msg)
                else:
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msg)
            except: pass

        if result.get("success"):
            filepath = result["filepath"]
            size_bytes = result["size"]
            size_mb = size_bytes / (1024*1024) if size_bytes else 0
            
            if size_bytes > 50 * 1024 * 1024:
                await edit_final_error(texts["too_large"].format(size=f"{size_mb:.1f}"))
                if os.path.exists(filepath): os.remove(filepath)
                async with LocalSession() as session:
                    await update_download_status(session, download_id, "failed", size_bytes)
                return
                
            try:
                async with LocalSession() as session:
                    await update_download_status(session, download_id, "done", size_bytes)
                
                with open(filepath, 'rb') as f:
                    if quality == 'mp3':
                        await bot.send_audio(chat_id=chat_id, audio=f, caption="✅ @Speeedloadbot")
                    elif quality == 'thumbnail':
                        await bot.send_photo(chat_id=chat_id, photo=f, caption="✅ @Speeedloadbot")
                    else:
                        await bot.send_video(chat_id=chat_id, video=f, caption="✅ @Speeedloadbot", supports_streaming=True)
                        
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                await edit_final_error(texts["generic_error"])
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            async with LocalSession() as session:
                await update_download_status(session, download_id, "failed")
            await edit_final_error(texts["generic_error"])
        await local_engine.dispose()
    asyncio.run(finalize())
