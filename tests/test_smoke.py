"""Smoke tests: every project module must import cleanly.

These catch syntax errors, broken imports and missing functions — the class
of bugs that previously prevented the bot from starting at all.
"""
import importlib

import pytest

MODULES = [
    "config",
    "database.connection",
    "database.models",
    "database.crud",
    "utils.translations",
    "utils.limits",
    "utils.safety",
    "utils.progress",
    "utils.human_touch",
    "utils.streak_system",
    "utils.integration",
    "utils.loading_messages",
    "utils.file_sizes",
    "utils.aicut",
    "utils.ffmpeg_tools",
    "downloader.detector",
    "downloader.youtube",
    "downloader.instagram",
    "downloader.universal",
    "bot.keyboards.reply",
    "bot.keyboards.inline",
    "bot.keyboards.onboarding",
    "bot.keyboards.creators",
    "bot.middlewares.rate_limit",
    "bot.handlers.start",
    "bot.handlers.onboarding",
    "bot.handlers.account",
    "bot.handlers.balance",
    "bot.handlers.referral",
    "bot.handlers.language",
    "bot.handlers.help",
    "bot.handlers.admin",
    "bot.handlers.creators",
    "bot.handlers.trends",
    "bot.handlers.download",
    "bot.jobs",
    "bot.main",
    "tasks.download_task",
    "api.main",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    importlib.import_module(module)


def test_transcriber_imports_if_whisper_available():
    # whisper (torch) is a heavy optional dependency — only test when installed
    pytest.importorskip("whisper")
    importlib.import_module("utils.transcriber")
