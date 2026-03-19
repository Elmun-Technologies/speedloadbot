from redis.asyncio import Redis
from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop
from config import REDIS_URL

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

async def check_rate_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
        
    user_id = user.id
    key = f"rl:{user_id}"
    
    current = await redis_client.get(key)
    if current and int(current) >= 3:
        if update.message:
            await update.message.reply_text("⏳ Iltimos, bir oz kuting. Bir daqiqada faqat 3 ta so'rov qabul qilinadi.")
        raise ApplicationHandlerStop()
        
    pipe = redis_client.pipeline()
    pipe.incr(key)
    if not current:
        pipe.expire(key, 60)
    await pipe.execute()
