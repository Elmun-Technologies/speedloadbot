"""Tests for the Celery worker tasks (tasks/download_task.py).

The tasks are executed synchronously in-process; the Telegram Bot class is
replaced with a fake so no network is touched.
"""
import asyncio

import pytest

pytest.importorskip("celery")

import tasks.download_task as tasks_module
from database.connection import AsyncSessionLocal


class FakeBot:
    """Records send_message calls instead of doing HTTP."""

    def __init__(self, token):
        self.token = token
        self.sent = []
        self.closed = False

    async def send_message(self, chat_id, text, parse_mode=None):
        self.sent.append({"chat_id": chat_id, "text": text, "parse_mode": parse_mode})

    async def shutdown(self):
        self.closed = True


def test_notify_ticket_reply_sends_telegram_message(monkeypatch):
    sent = []

    class RecordingFakeBot(FakeBot):
        def __init__(self, token):
            super().__init__(token)
            sent.append(self)

    monkeypatch.setattr(tasks_module, "Bot", RecordingFakeBot)
    monkeypatch.setattr(tasks_module, "BOT_TOKEN", "123456:test-token")

    tasks_module.notify_ticket_reply(telegram_id=42, message="Muammo hal qilindi", language="uz")

    assert len(sent) == 1
    bot = sent[0]
    assert len(bot.sent) == 1
    msg = bot.sent[0]
    assert msg["chat_id"] == 42
    assert msg["parse_mode"] == "HTML"
    assert "Muammo hal qilindi" in msg["text"]
    assert bot.closed  # the bot connection was shut down


def test_notify_ticket_reply_escapes_html_in_admin_message(monkeypatch):
    """The admin's reply text is HTML-escaped before being sent with
    parse_mode=HTML (no markup injection into Telegram)."""
    holder = []

    class RecordingFakeBot(FakeBot):
        def __init__(self, token):
            super().__init__(token)
            holder.append(self)

    monkeypatch.setattr(tasks_module, "Bot", RecordingFakeBot)
    monkeypatch.setattr(tasks_module, "BOT_TOKEN", "123456:test-token")

    tasks_module.notify_ticket_reply(telegram_id=7, message="<b>bold</b> & co", language="en")

    text = holder[0].sent[0]["text"]
    assert "&lt;b&gt;bold&lt;/b&gt;" in text  # escaped
    assert "<b>bold</b>" not in text         # raw markup is gone
    assert "Support reply" in text           # the en template label


def test_notify_ticket_reply_uses_user_language(monkeypatch):
    holder = []

    class RecordingFakeBot(FakeBot):
        def __init__(self, token):
            super().__init__(token)
            holder.append(self)

    monkeypatch.setattr(tasks_module, "Bot", RecordingFakeBot)
    monkeypatch.setattr(tasks_module, "BOT_TOKEN", "123456:test-token")

    tasks_module.notify_ticket_reply(telegram_id=7, message="xabar", language="ru")
    assert "Ответ от поддержки" in holder[0].sent[0]["text"]


# ---------------------------------------------------------------------------
# process_download — the worker's main task, end-to-end (real SQLite DB,
# faked download_media + faked Telegram Bot)
# ---------------------------------------------------------------------------

class WorkerFakeBot(FakeBot):
    """Fake bot for the download worker: records every Telegram call."""

    def __init__(self, token):
        super().__init__(token)
        self.calls = []

    async def edit_message_caption(self, **kw):
        self.calls.append(("edit_caption", kw))

    async def edit_message_text(self, **kw):
        self.calls.append(("edit_text", kw))

    async def send_video(self, **kw):
        self.calls.append(("send_video", kw))

    async def send_audio(self, **kw):
        self.calls.append(("send_audio", kw))

    async def send_photo(self, **kw):
        self.calls.append(("send_photo", kw))

    async def delete_message(self, **kw):
        self.calls.append(("delete", kw))


def _seed_download(tg_id):
    """Create a user + a pending download row; return the download id."""
    from database import crud

    async def run():
        async with AsyncSessionLocal() as s:
            user = await crud.create_user(s, tg_id, "worker", "Worker", "uz")
            row = await crud.create_download(
                s, user.id, "https://youtu.be/abc", "youtube", "720p", "Video", 60)
            await s.commit()
            return row.id

    return asyncio.run(run())


def _run_process_download(monkeypatch, tmp_path, quality, result, tg_id):
    """Run process_download with faked boundaries; return (bot, download_id)."""
    import asyncio as _asyncio

    from database.connection import init_db

    _asyncio.run(init_db())
    download_id = _seed_download(tg_id)

    monkeypatch.setattr(tasks_module, "download_media",
                        lambda url, quality, platform, progress_hook: result)
    bots = []

    class RecordingBot(WorkerFakeBot):
        def __init__(self, token):
            super().__init__(token)
            bots.append(self)

    monkeypatch.setattr(tasks_module, "Bot", RecordingBot)
    monkeypatch.setattr(tasks_module, "BOT_TOKEN", "123456:test-token")

    tasks_module.process_download(
        telegram_id=tg_id, chat_id=tg_id, message_id=5,
        url="https://youtu.be/abc", quality=quality,
        download_id=download_id, language="uz")
    return bots[0], download_id


def _download_status(download_id):
    from database.models import Download

    async def run():
        async with AsyncSessionLocal() as s:
            row = await s.get(Download, download_id)
            return row.status

    return asyncio.run(run())


def test_process_download_success_sends_video_and_marks_done(monkeypatch, tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake-video-bytes")

    bot, download_id = _run_process_download(
        monkeypatch, tmp_path, "720p",
        {"success": True, "filepath": str(video), "size": 2048}, tg_id=777001)

    kinds = [kind for kind, _ in bot.calls]
    assert "send_video" in kinds
    assert "delete" in kinds
    send = [kw for kind, kw in bot.calls if kind == "send_video"][0]
    assert send["chat_id"] == 777001  # noqa: E501
    assert bot.closed                      # bot session was shut down
    assert not video.exists()              # temp file cleaned up
    assert _download_status(download_id).value == "done"


def test_process_download_mp3_sends_audio(monkeypatch, tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"fake-audio")

    bot, download_id = _run_process_download(
        monkeypatch, tmp_path, "mp3",
        {"success": True, "filepath": str(audio), "size": 1024}, tg_id=777002)

    kinds = [kind for kind, _ in bot.calls]
    assert "send_audio" in kinds
    assert "send_video" not in kinds
    assert _download_status(download_id).value == "done"


def test_process_download_too_large_fails_safely(monkeypatch, tmp_path):
    video = tmp_path / "huge.mp4"
    video.write_bytes(b"x")

    bot, download_id = _run_process_download(
        monkeypatch, tmp_path, "1080p",
        {"success": True, "filepath": str(video), "size": 60 * 1024 * 1024}, tg_id=777003)

    kinds = [kind for kind, _ in bot.calls]
    assert "edit_caption" in kinds         # user told the file is too large
    assert "send_video" not in kinds       # never sent
    assert not video.exists()              # temp file removed
    assert bot.closed
    assert _download_status(download_id).value == "failed"


def test_process_download_failure_marks_failed_and_notifies(monkeypatch, tmp_path):
    bot, download_id = _run_process_download(
        monkeypatch, tmp_path, "720p", {"success": False}, tg_id=777004)

    kinds = [kind for kind, _ in bot.calls]
    assert "edit_caption" in kinds         # generic error shown to the user
    assert "send_video" not in kinds
    assert bot.closed
    assert _download_status(download_id).value == "failed"
