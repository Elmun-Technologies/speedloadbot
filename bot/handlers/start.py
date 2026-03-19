import random
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import AsyncSessionLocal
from database.crud import get_user, create_user, create_referral, get_user_by_ref_code
from utils.translations import TEXTS
from bot.keyboards.reply import get_main_menu
from utils.human_touch import send_typing

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await send_typing(context, chat_id, 0.5)
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        
        if not db_user:
            # Check referral
            referred_by = None
            referrer_tg_id = None
            referrer_lang = 'uz'
            if context.args and context.args[0].startswith("ref_"):
                ref_code = context.args[0].replace("ref_", "")
                referrer = await get_user_by_ref_code(session, ref_code)
                if referrer:
                    referred_by = referrer.id
                    referrer_tg_id = referrer.telegram_id
                    referrer_lang = referrer.language

            db_user = await create_user(
                session, 
                user.id, 
                user.username, 
                user.first_name, 
                user.language_code,
                referred_by
            )
            
            if referred_by:
                await create_referral(session, referred_by, db_user.id)
                # Award points to referrer
                from utils.integration import process_user_action
                await process_user_action(referrer_tg_id, 'referral', context.bot, referrer_lang)

            # Trigger Onboarding for new users
            from bot.handlers.onboarding import start_onboarding
            return await start_onboarding(update, context)

        # For existing users, check if onboarding is completed
        if not db_user.onboarding_completed:
            from bot.handlers.onboarding import start_onboarding
            return await start_onboarding(update, context)

        lang = db_user.language
        from utils.human_touch import get_smart_greeting
        from utils.integration import process_user_action
        
        text = get_smart_greeting(user.first_name, user.id)
        await process_user_action(user.id, 'daily_login', context.bot, lang)
        
        await update.message.reply_text(
            text, 
            reply_markup=get_main_menu(lang),
            parse_mode="HTML" # Improved emojis/links support
        )
