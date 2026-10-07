"""Unit tests for pure utility logic (no network, no database)."""
from datetime import date, datetime, timedelta

from database.models import (
    Download, Payment, Referral, Ticket, TicketReply, Trend, TrendView, User,
)
from downloader.detector import detect_platform
from utils.human_touch import (
    check_content_filter, detect_video_type, get_random_reaction,
)
from utils.progress import build_progress_bar
from utils.streak_system import get_level, update_streak_logic


# --- platform detection ---

def test_detect_platform_youtube():
    assert detect_platform("https://www.youtube.com/watch?v=abc123") == "youtube"
    assert detect_platform("https://youtu.be/abc123") == "youtube"


def test_detect_platform_instagram():
    assert detect_platform("https://www.instagram.com/reel/ABC123/") == "instagram"


def test_detect_platform_tiktok():
    assert detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"


def test_detect_platform_other():
    assert detect_platform("https://example.com/video") == "other"


# --- video type reactions ---

def test_detect_video_type():
    assert detect_video_type("Official Music Video", "") == "music"
    assert detect_video_type("Python darsi #1", "") == "education"
    assert detect_video_type("Some random vlog", "") == "general"


def test_get_random_reaction_returns_string():
    for v_type in ("music", "education", "gaming", "news", "tech",
                   "entertainment", "general", "unknown-type"):
        reaction = get_random_reaction(v_type)
        assert isinstance(reaction, str) and reaction


# --- content filter ---

def test_content_filter_blocks_harmful():
    res = check_content_filter("https://pornhub.com/video")
    assert res["triggered"] is True
    assert res["message"]


def test_content_filter_allows_normal_link():
    res = check_content_filter("https://youtube.com/watch?v=abc")
    assert res["triggered"] is False


# --- streak logic ---

def _fresh_user_data():
    return {
        "streak_days": 0,
        "streak_last_date": None,
        "streak_longest": 0,
        "daily_downloads": 0,
        "daily_creator_uses": 0,
        "daily_reset_date": None,
        "weekly_downloads": 0,
        "weekly_reset_date": None,
        "total_points": 0,
    }


def test_streak_first_action_starts_streak():
    updated, notifications = update_streak_logic(_fresh_user_data())
    assert updated["streak_days"] == 1
    assert updated["streak_longest"] == 1
    assert "new_streak" in notifications


def test_streak_same_day_does_not_double_count():
    data = _fresh_user_data()
    data["streak_days"] = 3
    data["streak_last_date"] = date.today()
    updated, notifications = update_streak_logic(data)
    assert updated["streak_days"] == 3
    assert notifications == []


def test_streak_consecutive_day_increments():
    data = _fresh_user_data()
    data["streak_days"] = 2
    data["streak_last_date"] = date.today() - timedelta(days=1)
    updated, notifications = update_streak_logic(data)
    assert updated["streak_days"] == 3
    assert "streak_3" in notifications


def test_streak_broken_resets_to_one():
    data = _fresh_user_data()
    data["streak_days"] = 10
    data["streak_last_date"] = date.today() - timedelta(days=3)
    updated, notifications = update_streak_logic(data)
    assert updated["streak_days"] == 1
    assert "streak_broken" in notifications


# --- levels ---

def test_get_level_boundaries():
    assert get_level(0)["level"] == 1
    assert get_level(99)["level"] == 1
    assert get_level(100)["level"] == 2
    assert get_level(12000)["level"] == 8


# --- progress bar ---

def test_build_progress_bar():
    assert build_progress_bar(0) == "░" * 10 + " 0%"
    assert build_progress_bar(100) == "█" * 10 + " 100%"
    assert build_progress_bar(50) == "█" * 5 + "░" * 5 + " 50%"


# --- model defaults must be callables (not fixed values) ---

def test_datetime_column_defaults_are_callable():
    """`default=datetime.utcnow` (without parentheses) would freeze the import
    time as the value for every row — defaults must be callables."""
    for model in (User, Download, Referral, Trend, TrendView, Ticket, TicketReply, Payment):
        for column in model.__table__.columns:
            if column.default is not None and hasattr(column.default, "arg"):
                assert callable(column.default.arg) or not isinstance(column.default.arg, datetime), (
                    f"{model.__name__}.{column.name} has a fixed datetime default"
                )
