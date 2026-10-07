"""End-to-end bot flow test: /start onboarding -> link -> quality -> DB record.

Runs the real application (handlers, conversation flows, rate limiter) against
a real SQLite database. Only the outer boundaries are faked:
- the Telegram HTTP API (FakeBot records calls instead of doing HTTP)
- yt-dlp extraction (returns canned video info)
- the Celery task queue (records the queued download)
"""
import asyncio
import json
from datetime import datetime

import pytest

pytest.importorskip("aiosqlite")
pytest.importorskip("fakeredis")

import fakeredis.aioredis
from sqlalchemy import select
from telegram import Bot, Update

import bot.handlers.download as download_module
import bot.middlewares.rate_limit as rate_limit_module
from bot.main import build_application
from database import crud
from database.connection import AsyncSessionLocal, init_db
from database.models import Download, DownloadStatus

USER_ID = 555001
RETURNING_USER_ID = 555002
BANNED_USER_ID = 555003
COMPLETED_USER_ID = 555004
PLAIN_USER_ID = 555005
BOT_ID = 999999
LINK = "https://www.youtube.com/watch?v=abc123"

FAKE_YT_INFO = {
    "title": "Test Video",
    "uploader": "TestChannel",
    "duration": 95,
    "view_count": 12345,
    "thumbnail": "https://example.com/thumb.jpg",
}
FAKE_SIZES = {"360p": 10.5, "720p": 45.2, "1080p": 98.0, "mp3": 3.1}


class FakeBot(Bot):
    """A Bot that never touches the network: records API calls and returns
    canned responses so the whole handler chain can run offline."""

    def __init__(self):
        super().__init__(token="123456:ABCfake-token-for-tests")
        self._calls = []  # list of (endpoint, data-dict)
        self._next_message_id = 1000

    async def _post(self, endpoint, data=None, **kwargs):
        data = dict(data or {})
        self._calls.append((endpoint, data))

        if endpoint == "getMe":
            return {
                "id": BOT_ID,
                "is_bot": True,
                "first_name": "SpeedLoadTestBot",
                "username": "speedload_test_bot",
            }
        if endpoint in ("sendMessage", "editMessageText", "editMessageCaption"):
            self._next_message_id += 1
            result = {
                "message_id": self._next_message_id,
                "date": int(datetime.now().timestamp()),
                "chat": {"id": data.get("chat_id"), "type": "private"},
                "text": data.get("text") or data.get("caption") or "",
            }
            reply_to = data.get("reply_to_message_id")
            if reply_to:
                result["reply_to_message"] = {
                    "message_id": reply_to,
                    "date": int(datetime.now().timestamp()),
                    "chat": {"id": data.get("chat_id"), "type": "private"},
                    "text": "",
                }
            return result
        return True

    # --- assertion helpers ---
    def sent_messages(self):
        return [data for endpoint, data in self._calls if endpoint == "sendMessage"]

    def edited_texts(self):
        return [data for endpoint, data in self._calls if endpoint == "editMessageText"]

    @staticmethod
    def _markup(data):
        # _post intercepts BEFORE PTB serializes, so reply_markup is still a
        # TelegramObject (ReplyKeyboardMarkup / InlineKeyboardMarkup).
        markup = data.get("reply_markup")
        if markup is None:
            return {}
        if isinstance(markup, str):
            markup = json.loads(markup)
        if hasattr(markup, "to_dict"):
            markup = markup.to_dict()
        return markup if isinstance(markup, dict) else {}

    def inline_buttons(self, data):
        markup = self._markup(data)
        return [
            btn.get("callback_data")
            for row in markup.get("inline_keyboard", [])
            for btn in row
        ]

    def reply_buttons(self, data):
        markup = self._markup(data)
        return [
            btn.get("text")
            for row in markup.get("keyboard", [])
            for btn in row
        ]


class FakeTask:
    """Stands in for the Celery task: records .delay() calls."""

    def __init__(self):
        self.delay_calls = []

    def delay(self, **kwargs):
        self.delay_calls.append(kwargs)


def make_bot():
    return FakeBot()


def patch_boundaries(monkeypatch, bot):
    """Fake the outer boundaries: Redis, Celery, yt-dlp."""
    monkeypatch.setattr(
        rate_limit_module, "redis_client", fakeredis.aioredis.FakeRedis(decode_responses=True)
    )
    fake_task = FakeTask()
    monkeypatch.setattr(download_module, "process_download", fake_task)
    monkeypatch.setattr(download_module, "extract_youtube_info", lambda url: FAKE_YT_INFO)
    monkeypatch.setattr(download_module, "get_format_sizes", lambda url: FAKE_SIZES)
    return fake_task


def message_update(text, message_id, bot, user_id=USER_ID, entities=None):
    payload = {
        "update_id": message_id,
        "message": {
            "message_id": message_id,
            "date": int(datetime.now().timestamp()),
            "chat": {"id": user_id, "type": "private"},
            "from": {"id": user_id, "is_bot": False, "first_name": "Test"},
            "text": text,
        },
    }
    if entities:
        payload["message"]["entities"] = entities
    return Update.de_json(payload, bot)


def callback_update(data, message_id, bot, user_id=USER_ID, reply_to_message_id=None):
    msg = {
        "message_id": message_id,
        "date": int(datetime.now().timestamp()),
        "chat": {"id": user_id, "type": "private"},
        "from": {
            "id": BOT_ID, "is_bot": True,
            "first_name": "SpeedLoadTestBot", "username": "speedload_test_bot",
        },
        "text": "card",
    }
    if reply_to_message_id:
        msg["reply_to_message"] = {
            "message_id": reply_to_message_id,
            "date": int(datetime.now().timestamp()),
            "chat": {"id": user_id, "type": "private"},
            "text": LINK,
        }
    payload = {
        "update_id": message_id + 500,
        "callback_query": {
            "id": f"cb-{message_id}",
            "from": {"id": user_id, "is_bot": False, "first_name": "Test"},
            "chat_instance": "ci",
            "data": data,
            "message": msg,
        },
    }
    return Update.de_json(payload, bot)


def test_full_onboarding_and_download_flow(monkeypatch):
    bot = make_bot()
    fake_task = patch_boundaries(monkeypatch, bot)
    app = build_application(bot=bot)

    async def scenario():
        await init_db()
        await app.initialize()

        # --- 1. New user sends /start ---
        await app.process_update(message_update(
            "/start", 1, bot,
            entities=[{"type": "bot_command", "offset": 0, "length": 6}],
        ))
        lang_keyboards = [m for m in bot.sent_messages() if m.get("reply_markup")]
        assert any("lang_uz" in bot.inline_buttons(m) for m in lang_keyboards)

        # --- 2. Pick language: ru ---
        await app.process_update(callback_update("lang_ru", 100, bot))
        assert any(
            "interest_business" in bot.inline_buttons(m) for m in bot.sent_messages()
        )

        # --- 3. Pick interest ---
        await app.process_update(callback_update("interest_business", 101, bot))

        # --- 4. Pick occupation -> onboarding complete ---
        await app.process_update(callback_update("occ_student", 102, bot))

        async with AsyncSessionLocal() as s:
            user = await crud.get_user(s, USER_ID)
            assert user is not None
            assert user.onboarding_completed is True
            assert user.language == "ru"
            assert user.interests == "business"
            assert user.occupation == "student"

        # --- 5. Send a YouTube link ---
        await app.process_update(message_update(LINK, 200, bot))

        # the video info card was sent with the quality keyboard attached
        edits = bot.edited_texts()
        assert edits, "expected the info card to be edited in"
        card = edits[-1]
        buttons = bot.inline_buttons(card)
        assert "quality_720p" in buttons
        assert "quality_mp3" in buttons
        assert "Test Video" in (card.get("text") or "")

        # --- 6. Tap a quality button ---
        await app.process_update(
            callback_update("quality_720p", 300, bot, reply_to_message_id=200)
        )

        # the download was queued with the right arguments
        assert len(fake_task.delay_calls) == 1
        call = fake_task.delay_calls[0]
        assert call["telegram_id"] == USER_ID
        assert call["url"] == LINK
        assert call["quality"] == "720p"

        # download row + gamification persisted in the DB
        async with AsyncSessionLocal() as s:
            user = await crud.get_user(s, USER_ID)
            assert user.total_downloads == 1
            assert user.total_points >= 5
            rows = (await s.execute(select(Download))).scalars().all()
            assert len(rows) == 1
            assert rows[0].status == DownloadStatus.pending
            assert rows[0].platform == "youtube"
            assert rows[0].quality == "720p"
            assert rows[0].url == LINK

        await app.shutdown()

    asyncio.run(scenario())


def test_returning_user_gets_main_menu(monkeypatch):
    bot = make_bot()
    patch_boundaries(monkeypatch, bot)
    app = build_application(bot=bot)

    async def scenario():
        await init_db()
        # pre-create a fully onboarded user
        async with AsyncSessionLocal() as s:
            await crud.create_user(s, RETURNING_USER_ID, "ret", "Ret", "uz")
            user = await crud.get_user(s, RETURNING_USER_ID)
            await crud.update_user_profile(s, user.id, onboarding_completed=True)

        await app.initialize()

        await app.process_update(message_update(
            "/start", 1, bot, user_id=RETURNING_USER_ID,
            entities=[{"type": "bot_command", "offset": 0, "length": 6}],
        ))

        sent = bot.sent_messages()
        # main menu (reply keyboard) was sent...
        assert any("📥 Yuklab olish" in bot.reply_buttons(m) for m in sent)
        # ...and onboarding was NOT restarted (no language keyboard)
        assert not any("lang_uz" in bot.inline_buttons(m) for m in sent)

        await app.shutdown()

    asyncio.run(scenario())


async def _make_onboarded_user(user_id, username, banned=False):
    async with AsyncSessionLocal() as s:
        await crud.create_user(s, user_id, username, "Test", "uz")
        user = await crud.get_user(s, user_id)
        await crud.update_user_profile(s, user.id, onboarding_completed=True)
        if banned:
            user.is_banned = True
            await s.commit()


def test_banned_user_is_blocked_in_bot(monkeypatch):
    """Banned users get a 'blocked' notice and cannot use the bot at all —
    neither /start nor link processing (previously they were only excluded
    from broadcasts/jobs)."""
    bot = make_bot()
    fake_task = patch_boundaries(monkeypatch, bot)
    app = build_application(bot=bot)

    async def scenario():
        await init_db()
        await _make_onboarded_user(BANNED_USER_ID, "banned", banned=True)
        await app.initialize()

        # /start -> banned notice, no menu keyboards
        await app.process_update(message_update(
            "/start", 1, bot, user_id=BANNED_USER_ID,
            entities=[{"type": "bot_command", "offset": 0, "length": 6}],
        ))
        sent = bot.sent_messages()
        assert any("🚫" in (m.get("text") or "") for m in sent)
        assert not any("📥 Yuklab olish" in bot.reply_buttons(m) for m in sent)
        assert not any("lang_uz" in bot.inline_buttons(m) for m in sent)

        # a YouTube link -> banned notice again, no extraction, no download
        await app.process_update(message_update(LINK, 2, bot, user_id=BANNED_USER_ID))
        sent = bot.sent_messages()
        assert any("🚫" in (m.get("text") or "") for m in sent)
        assert not bot.edited_texts()          # no info card was sent
        assert fake_task.delay_calls == []     # nothing was queued

        await app.shutdown()

    asyncio.run(scenario())


def test_unsupported_link_gets_error_reply(monkeypatch):
    """A link from an unsupported platform gets the 'unsupported' notice
    and never reaches yt-dlp."""
    bot = make_bot()
    fake_task = patch_boundaries(monkeypatch, bot)
    app = build_application(bot=bot)

    async def scenario():
        await init_db()
        await _make_onboarded_user(COMPLETED_USER_ID, "comp")
        await app.initialize()

        await app.process_update(
            message_update("https://example.com/video", 1, bot, user_id=COMPLETED_USER_ID)
        )
        sent = bot.sent_messages()
        assert any("❌" in (m.get("text") or "") for m in sent)
        assert not bot.edited_texts()
        assert fake_task.delay_calls == []

        await app.shutdown()

    asyncio.run(scenario())


def test_plain_text_gets_no_reply(monkeypatch):
    """A plain (non-link) message is ignored silently by the download handler."""
    bot = make_bot()
    patch_boundaries(monkeypatch, bot)
    app = build_application(bot=bot)

    async def scenario():
        await init_db()
        await _make_onboarded_user(PLAIN_USER_ID, "plain")
        await app.initialize()

        await app.process_update(
            message_update("salom, qalaysan?", 1, bot, user_id=PLAIN_USER_ID)
        )
        assert bot.sent_messages() == []

        await app.shutdown()

    asyncio.run(scenario())
