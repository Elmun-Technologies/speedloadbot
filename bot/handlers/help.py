from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database.connection import AsyncSessionLocal
from database.models import User, Ticket, TicketType
from utils.translations import TEXTS
from utils.human_touch import send_typing
from bot.keyboards.inline import get_help_keyboard

# States
GET_TICKET = 1

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await send_typing(context, chat_id, 0.5)
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        lang = db_user.language if db_user else "uz"
        
    texts = TEXTS.get(lang, TEXTS["uz"])
    await update.message.reply_text(texts["help_text"], reply_markup=get_help_keyboard(lang), parse_mode="Markdown")

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user_id)
        lang = db_user.language if db_user else "uz"
    
    texts = TEXTS.get(lang, TEXTS["uz"])
    
    if query.data == "help_tickets":
        await query.message.reply_text(texts["ticket_prompt"], parse_mode="Markdown")
        return GET_TICKET
        
    return ConversationHandler.END

async def ticket_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user.id)
        lang = db_user.language if db_user else "uz"
        
        if db_user:
            # Save to DB for Admin Panel
            ticket = Ticket(
                user_id=db_user.id,
                user_name=user.first_name,
                message=update.message.text or "File/Photo",
                type=TicketType.other
            )
            session.add(ticket)
            await session.commit()
    
    texts = TEXTS.get(lang, TEXTS["uz"])
    
    await send_typing(context, chat_id, 1.2)
    await update.message.reply_text(texts["ticket_thanks"], parse_mode="Markdown")
    
    return ConversationHandler.END

async def cancel_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

help_conv = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(f"^({TEXTS['uz']['btn_help']}|{TEXTS['ru']['btn_help']}|{TEXTS['en']['btn_help']})$"), help_handler),
        CallbackQueryHandler(help_callback, pattern="^help_")
    ],
    states={
        GET_TICKET: [
            MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, ticket_message_handler)
        ]
    },
    fallbacks=[MessageHandler(filters.COMMAND, cancel_help)],
    allow_reentry=True
)
