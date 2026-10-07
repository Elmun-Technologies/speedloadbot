"""Unit tests for the Redis-backed rate limiter (using fakeredis)."""
import asyncio
from datetime import datetime

import pytest

pytest.importorskip("fakeredis")

import fakeredis.aioredis
from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ApplicationBuilder

import bot.middlewares.rate_limit as rate_limit_module
from bot.middlewares.rate_limit import RateLimitedApplication


def make_message_update(user_id: int) -> Update:
    user = User(id=user_id, is_bot=False, first_name="Test")
    msg = Message(
        message_id=1, date=datetime.now(),
        chat=Chat(id=user_id, type="private"), from_user=user, text="hi",
    )
    return Update(update_id=1, message=msg)


def make_callback_update(user_id: int) -> Update:
    user = User(id=user_id, is_bot=False, first_name="Test")
    msg = Message(
        message_id=2, date=datetime.now(),
        chat=Chat(id=user_id, type="private"), from_user=user,
    )
    cq = CallbackQuery(id="cb", from_user=user, chat_instance="ci", message=msg, data="x")
    return Update(update_id=2, callback_query=cq)


def build_app() -> RateLimitedApplication:
    return (
        ApplicationBuilder()
        .token("123456:ABCdummy")
        .application_class(RateLimitedApplication)
        .build()
    )


def test_allows_up_to_limit_then_blocks(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(rate_limit_module, "redis_client", fake)
    app = build_app()

    async def body():
        u = make_message_update(42)
        assert await app._allow_update(u) is True
        assert await app._allow_update(u) is True
        assert await app._allow_update(u) is True
        assert await app._allow_update(u) is False  # 4th within the window
        # a different user is unaffected
        assert await app._allow_update(make_message_update(43)) is True

    asyncio.run(body())


def test_window_expires(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(rate_limit_module, "redis_client", fake)
    app = build_app()
    app.WINDOW_SECONDS = 1  # shorten the window for the test

    async def body():
        u = make_message_update(7)
        for _ in range(3):
            assert await app._allow_update(u) is True
        assert await app._allow_update(u) is False
        await asyncio.sleep(1.1)  # let the window expire
        assert await app._allow_update(u) is True

    asyncio.run(body())


def test_callback_queries_are_not_limited(monkeypatch):
    """Button taps must never be blocked — onboarding needs several in a row."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(rate_limit_module, "redis_client", fake)
    app = build_app()

    async def body():
        for _ in range(10):
            assert await app._allow_update(make_callback_update(9)) is True

    asyncio.run(body())


def test_fails_open_when_redis_is_down(monkeypatch):
    class BrokenRedis:
        async def get(self, key):
            raise ConnectionError("redis is down")

        def pipeline(self):
            raise ConnectionError("redis is down")

    monkeypatch.setattr(rate_limit_module, "redis_client", BrokenRedis())
    app = build_app()

    async def body():
        # must not raise — users are never blocked because of a Redis outage
        assert await app._allow_update(make_message_update(1)) is True

    asyncio.run(body())
