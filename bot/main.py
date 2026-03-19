import logging
import asyncio
from datetime import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import BOT_TOKEN
# Handler imports
from bot.handlers.start import start_handler
from bot.handlers.onboarding import onboarding_conv
from bot.handlers.account import account_handler, donate_callback_handler
from bot.handlers.referral import referral_handler
from bot.handlers.language import language_command, language_callback
from bot.handlers.download import message_handler, quality_callback, platform_callback
from bot.handlers.help import help_conv
from bot.handlers.admin import admin_handler, admin_callback_handler, admin_broadcast_conv
from bot.handlers.creators import creators_handler, creator_tool_router, file_handler
from bot.handlers.trends import trend_radar_handler, handle_trend_personalized, cmd_update_trends_ai
import pytz
from bot.jobs import morning_motivation_job, juma_greeting_job, weekly_challenge_job, weekly_trend_refresh

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def setup_db():
    await init_db()

async def global_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # 1. Check for creator tool buttons (intercepts reply keyboard)
    if await creator_tool_router(update, context):
        return
        
    # 2. Check for file uploads (if in creator state)
    if update.message.video or update.message.audio or update.message.document or update.message.photo:
        return await file_handler(update, context)

    # 3. Default downloader router
    return await message_handler(update, context)

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_db())

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Scheduler setup
    if app.job_queue:
        tz = pytz.timezone('Asia/Tashkent')
        # Morning motivation - 08:00 daily
        app.job_queue.run_daily(morning_motivation_job, time=time(hour=8, minute=0, tzinfo=tz))
        # Juma greeting - Friday 12:00
        app.job_queue.run_daily(juma_greeting_job, time=time(hour=12, minute=0, tzinfo=tz), days=(4,))
        # Weekly challenge - Monday 09:00
        app.job_queue.run_daily(weekly_challenge_job, time=time(hour=9, minute=0, tzinfo=tz), days=(0,))
        # Weekly Trend Refresh - Monday 08:00
        app.job_queue.run_daily(weekly_trend_refresh, time=time(hour=8, minute=0, tzinfo=tz), days=(0,))

    # Handlers
    # Onboarding (includes /start)
    app.add_handler(onboarding_conv)
    app.add_handler(help_conv)
    
    # Admin
    app.add_handler(CommandHandler("admin", admin_handler))
    app.add_handler(admin_broadcast_conv)
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_tickets$"))
    app.add_handler(CommandHandler("updatetrends", cmd_update_trends_ai))
    
    # Other Commands
    app.add_handler(CommandHandler("account", account_handler))
    app.add_handler(CommandHandler("stats", account_handler))
    app.add_handler(CallbackQueryHandler(donate_callback_handler, pattern="^donate_info$"))
    app.add_handler(CommandHandler("balance", account_handler))
    app.add_handler(CommandHandler("referral", referral_handler))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("creators", creators_handler))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(quality_callback, pattern="^quality_"))
    app.add_handler(CallbackQueryHandler(platform_callback, pattern="^plat_"))
    app.add_handler(CallbackQueryHandler(trend_radar_handler, pattern="^trend_radar_again$"))
    app.add_handler(CallbackQueryHandler(handle_personalized_trend, pattern="^trend_personalized$"))
    
    # Unified Message Handler
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, global_message_router))

    logging.info("Bot started.")
    app.run_polling()

if __name__ == '__main__':
    from database.connection import init_db
    main()
