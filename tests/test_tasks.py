"""Tests for the Celery worker tasks (tasks/download_task.py).

The tasks are executed synchronously in-process; the Telegram Bot class is
replaced with a fake so no network is touched.
"""
import pytest

pytest.importorskip("celery")

import tasks.download_task as tasks_module


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
