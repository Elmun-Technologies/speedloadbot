"""Unit tests for the pure helper functions in utils/human_touch.py."""
from datetime import datetime

import pytest

from utils.human_touch import (
    VIDEO_REACTIONS,
    check_content_filter,
    detect_video_type,
    format_profile,
    get_morning_message,
    get_nudge_message,
    get_quote,
    get_random_reaction,
    get_smart_greeting,
    get_weekly_challenge,
)


# --- content filter -------------------------------------------------------

def test_content_filter_clean_text_passes():
    res = check_content_filter("https://youtube.com/watch?v=abc", "uz")
    assert res["triggered"] is False
    assert res["message"] == ""


@pytest.mark.parametrize("lang", ["uz", "ru", "en"])
def test_content_filter_blocks_harmful_content_with_kind_warning(lang):
    res = check_content_filter("bu 1xbet da stavka", lang)
    assert res["triggered"] is True
    assert res["message"]  # a gentle redirect message, not empty


def test_content_filter_unknown_language_falls_back_to_uz():
    res = check_content_filter("casino", "xx")
    assert res["triggered"] is True
    assert "Do'stim" in res["message"]


# --- video type detection -------------------------------------------------

@pytest.mark.parametrize("title,expected", [
    ("Official Music Video", "music"),
    ("Klip — Qo'shiq klipi", "music"),
    ("Python darslik tutorial", "education"),
    ("Gameplay стрим прохождение", "gaming"),
    ("Yangiliklar news", "news"),
    ("Smartfon обзор", "tech"),
    ("Kulgili meme", "entertainment"),
    ("Some random video", "general"),
])
def test_detect_video_type(title, expected):
    assert detect_video_type(title) == expected


def test_detect_video_type_uses_uploader_too():
    assert detect_video_type("", "Pro Gamer") == "gaming"
    assert detect_video_type("", "Darslik TV") == "education"


def test_get_random_reaction_matches_video_type():
    assert get_random_reaction("music") in VIDEO_REACTIONS["music"]
    assert get_random_reaction("education") in VIDEO_REACTIONS["education"]
    # unknown type falls back to the general reactions
    assert get_random_reaction("no-such-type") in VIDEO_REACTIONS["general"]


# --- greetings & messages -------------------------------------------------

def test_get_smart_greeting_includes_name():
    assert "Ali" in get_smart_greeting("Ali", 12345)


def test_get_smart_greeting_fallback_name():
    msg = get_smart_greeting(None, 1)
    assert "Do'stim" in msg


def test_get_quote_all_languages():
    for lang in ("uz", "ru", "en"):
        assert get_quote(lang)


def test_get_morning_message_languages_and_fallback():
    assert get_morning_message("uz")
    assert get_morning_message("ru")
    assert get_morning_message("xx")  # falls back to uz


def test_get_weekly_challenge_non_empty():
    assert get_weekly_challenge("uz")


def test_get_nudge_message_trigger_and_skip(monkeypatch):
    # 30% trigger: force the "always" branch
    monkeypatch.setattr("utils.human_touch.random.random", lambda: 0.0)
    msg = get_nudge_message("download", "Ali", "uz")
    assert msg and "Ali" in msg
    # force the "skip" branch
    monkeypatch.setattr("utils.human_touch.random.random", lambda: 0.9)
    assert get_nudge_message("download", "Ali", "uz") is None


def test_get_nudge_message_unknown_feature_uses_general():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("utils.human_touch.random.random", lambda: 0.0)
    msg = get_nudge_message("no-such-feature", "Vali", "uz")
    assert msg and "Vali" in msg
    monkeypatch.undo()


# --- profile formatting ---------------------------------------------------

def test_format_profile_includes_user_fields():
    msg = format_profile({
        "name": "Ali", "id": 42, "join_date": datetime.now(),
        "downloads": 120, "creator_uses": 0, "referrals": 1,
        "credits": 5, "streak": 3,
    }, "uz")
    assert "Ali" in msg
    assert "42" in msg
    assert "Gold" in msg  # 120 downloads -> Gold Ijodkor status
