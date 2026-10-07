"""Integration tests for the CRUD layer against a real (SQLite) database.

Runs the actual CRUD functions end-to-end: user creation, referrals, downloads,
limits/resets, credits, trends. Skipped automatically if aiosqlite is missing.
"""
import asyncio
from datetime import datetime, timedelta

import pytest

pytest.importorskip("aiosqlite")

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import crud
from database.connection import Base
from database.models import Download, DownloadStatus, User


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(setup())
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    asyncio.run(engine.dispose())


def run(coro):
    asyncio.run(coro)


def test_create_and_get_user(session_factory):
    async def body():
        async with session_factory() as s:
            user = await crud.create_user(s, 111, "ali", "Ali", "uz")
            assert user.telegram_id == 111
            assert user.username == "ali"
            assert user.language == "uz"
            assert len(user.referral_code) == 12
            assert user.credits == 5

            fetched = await crud.get_user(s, 111)
            assert fetched is not None and fetched.id == user.id
            assert await crud.get_user(s, 999) is None

    run(body())


def test_create_user_language_normalization(session_factory):
    async def body():
        async with session_factory() as s:
            assert (await crud.create_user(s, 1, "a", "A", "en-US")).language == "en"
            assert (await crud.create_user(s, 2, "b", "B", "ru-RU")).language == "ru"
            assert (await crud.create_user(s, 3, "c", "C", "xx")).language == "uz"

    run(body())


def test_referral_flow(session_factory):
    async def body():
        async with session_factory() as s:
            referrer = await crud.create_user(s, 100, "ref", "Ref", "uz")
            newcomer = await crud.create_user(s, 200, "new", "New", "uz", referred_by=referrer.id)

            await crud.create_referral(s, referrer.id, newcomer.id)
            count, earned = await crud.get_referral_stats(s, referrer.id)
            assert count == 1 and earned == 2

            by_code = await crud.get_user_by_ref_code(s, referrer.referral_code)
            assert by_code.id == referrer.id
            assert await crud.get_user_by_ref_code(s, "no-such-code") is None

    run(body())


def test_download_lifecycle(session_factory):
    async def body():
        async with session_factory() as s:
            user = await crud.create_user(s, 300, "dl", "Dl", "uz")
            dl = await crud.create_download(
                s, user.id, "https://youtu.be/x", "youtube", "720p", "Title", 42
            )
            assert dl.status == DownloadStatus.pending

            await crud.update_download_status(s, dl.id, "done", 123456)
            updated = await s.get(Download, dl.id)
            assert updated.status == DownloadStatus.done
            assert updated.file_size == 123456
            assert updated.platform == "youtube"

    run(body())


def test_check_and_deduct_limit(session_factory):
    async def body():
        async with session_factory() as s:
            user = await crud.create_user(s, 400, "lim", "Lim", "uz")
            # fresh user: 5 downloads per 6h window
            for _ in range(5):
                assert await crud.check_and_deduct_limit(s, user) is True
            # exhausted
            assert await crud.check_and_deduct_limit(s, user) is False
            # referral bonus grants one free download
            user.referral_bonus = 1
            assert await crud.check_and_deduct_limit(s, user) is True
            assert user.referral_bonus == 0

    run(body())


def test_get_limits_applies_time_resets(session_factory):
    async def body():
        async with session_factory() as s:
            await crud.create_user(s, 500, "res", "Res", "uz")
            user = await crud.get_user(s, 500)
            user.downloads_6h = 0
            user.last_6h_reset = datetime.utcnow() - timedelta(hours=7)
            user.downloads_week = 50
            user.last_week_reset = datetime.utcnow() - timedelta(days=8)
            await s.commit()

            limits = await crud.get_limits(s, 500)
            assert limits["downloads_6h"] == 5
            assert limits["downloads_week"] == 0

    run(body())


def test_trends_crud(session_factory):
    async def body():
        async with session_factory() as s:
            await crud.add_trend(s, {
                "week_number": "2026-W15", "category": "music", "title": "Trend A",
                "description": "d", "growth_percent": 250, "how_to_use": "x", "lang": "uz",
            })
            await crud.add_trend(s, {
                "week_number": "2026-W15", "category": "format", "title": "Trend B",
                "description": "d", "growth_percent": 100, "how_to_use": "x", "lang": "uz",
            })
            trends = await crud.get_active_trends(s, "2026-W15", "uz")
            assert len(trends) == 2
            assert trends[0].title == "Trend A"  # ordered by growth desc

            await crud.deactivate_old_trends(s, "2026-W16")
            assert await crud.get_active_trends(s, "2026-W15", "uz") == []

            view = await crud.log_trend_view(s, 123, trends[0].id)
            assert view.trend_id == trends[0].id

    run(body())


def test_add_credits_uses_telegram_id(session_factory):
    async def body():
        async with session_factory() as s:
            await crud.create_user(s, 600, "cred", "Cred", "uz")
            updated = await crud.add_credits(s, 600, 10)
            assert updated.credits == 15
            assert updated.creator_credits == 13
            assert await crud.add_credits(s, 999, 5) is None

    run(body())


def test_update_language_and_profile(session_factory):
    async def body():
        async with session_factory() as s:
            user = await crud.create_user(s, 700, "lang", "Lang", "uz")
            await crud.update_user_language(s, user.id, "ru")
            await crud.update_user_profile(
                s, user.id, occupation="student", onboarding_completed=True
            )
            fresh = await crud.get_user(s, 700)
            assert fresh.language == "ru"
            assert fresh.occupation == "student"
            assert fresh.onboarding_completed is True

    run(body())


def test_top_users_and_active_users(session_factory):
    async def body():
        async with session_factory() as s:
            u1 = await crud.create_user(s, 801, "a", "A", "uz")
            u2 = await crud.create_user(s, 802, "b", "B", "uz")
            u1.weekly_downloads = 30
            u2.weekly_downloads = 99
            u1.last_active = datetime.utcnow()
            u2.last_active = datetime.utcnow() - timedelta(days=30)
            await s.commit()

            top = await crud.get_top_users_by_downloads(s, limit=1)
            assert top[0].telegram_id == 802

            active = await crud.get_active_users_for_notification(s, days=7)
            assert [u.telegram_id for u in active] == [801]

    run(body())


def test_increment_creator_uses(session_factory):
    async def body():
        async with session_factory() as s:
            user = await crud.create_user(s, 900, "cu", "Cu", "uz")
            updated = await crud.increment_creator_uses(s, user.id)
            assert updated.total_creator_uses == 1

    run(body())
