import logging

from redis.asyncio import Redis
from telegram import Update
from telegram.ext import Application

from config import REDIS_URL

logger = logging.getLogger(__name__)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


class RateLimitedApplication(Application):
    """
    `Application` subclass that enforces a per-user rate limit before any
    handler runs: each user may send at most `MAX_REQUESTS` messages per
    `WINDOW_SECONDS` seconds. Fails open if Redis is unavailable, so a Redis
    outage never blocks users.

    python-telegram-bot v20+ has no custom-middleware API, so the limit is
    enforced by overriding `Application.process_update` — the single funnel
    every update passes through.
    """

    MAX_REQUESTS = 3
    WINDOW_SECONDS = 60

    async def process_update(self, update: object) -> None:
        if isinstance(update, Update) and not await self._allow_update(update):
            if update.message:
                await update.message.reply_text(
                    "⏳ Iltimos, bir oz kuting. Bir daqiqada faqat "
                    f"{self.MAX_REQUESTS} ta so'rov qabul qilinadi."
                )
            return  # drop the update — no handler runs
        await super().process_update(update)

    async def _allow_update(self, update: Update) -> bool:
        user = update.effective_user
        # Only messages are rate-limited. Callback-query button taps are cheap
        # and must stay unlimited — otherwise multi-step flows like onboarding
        # (which needs 4 taps) would get blocked. The expensive path (link
        # extraction via yt-dlp) is always triggered by a message.
        # NOTE: update.effective_message also resolves to the callback query's
        # message, so we must check the raw message fields instead.
        if not user or not (update.message or update.edited_message):
            return True
        key = f"rl:{user.id}"
        try:
            current = await redis_client.get(key)
            if current and int(current) >= self.MAX_REQUESTS:
                return False
            pipe = redis_client.pipeline()
            pipe.incr(key)
            if not current:
                pipe.expire(key, self.WINDOW_SECONDS)
            await pipe.execute()
            return True
        except Exception:
            logger.warning("Rate limiter: Redis unavailable — failing open", exc_info=True)
            return True
