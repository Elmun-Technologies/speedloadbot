"""Tests for the scheduled bot jobs (bot/jobs.py) against a real SQLite DB.

Only the Telegram bot is faked — the user selection logic (active within 7
days, not banned) runs for real.
"""
import asyncio
import types
from datetime import datetime, timedelta

import pytest

pytest.importorskip("aiosqlite")

from bot.jobs import morning_motivation_job, weekly_challenge_job
from database import crud
from database.connection import AsyncSessionLocal, init_db


class FakeJobBot:
    def __init__(self):
        self.sent = []  # list of (chat_id, text)

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


async def _seed_users():
    """One active user, one inactive (10 days), one banned (recent)."""
    async with AsyncSessionLocal() as s:
        await crud.create_user(s, 7001, "active", "Active", "uz")
        await crud.create_user(s, 7002, "old", "Old", "uz")
        await crud.create_user(s, 7003, "banned", "Banned", "uz")
        old = await crud.get_user(s, 7002)
        banned = await crud.get_user(s, 7003)
        old.last_active = datetime.utcnow() - timedelta(days=10)
        banned.is_banned = True
        await s.commit()


def _run(coro):
    return asyncio.run(coro)


def test_morning_motivation_reaches_only_active_non_banned_users():
    async def scenario():
        await init_db()
        await _seed_users()

        bot = FakeJobBot()
        await morning_motivation_job(types.SimpleNamespace(bot=bot))

        chat_ids = [chat_id for chat_id, _ in bot.sent]
        # the shared session DB may hold users from other test files — what
        # matters is the filtering behavior:
        assert 7001 in chat_ids      # active, not banned -> notified
        assert 7002 not in chat_ids  # inactive (10 days) -> excluded
        assert 7003 not in chat_ids  # banned -> excluded
        assert all(text for _, text in bot.sent)

    _run(scenario())


def test_weekly_challenge_reaches_only_active_non_banned_users():
    async def scenario():
        bot = FakeJobBot()
        await weekly_challenge_job(types.SimpleNamespace(bot=bot))

        chat_ids = [chat_id for chat_id, _ in bot.sent]
        assert 7001 in chat_ids
        assert 7002 not in chat_ids
        assert 7003 not in chat_ids

    _run(scenario())
