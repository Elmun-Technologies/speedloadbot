"""Conversation wiring tests: entry points and state handlers match correctly.

Note: ConversationHandler.check_update only consults state handlers when a
conversation is already active, so we check the individual handlers directly —
this verifies the wiring without needing a running bot.
"""
from datetime import datetime

from telegram import CallbackQuery, Chat, Message, Update, User

from bot.handlers.admin import BROADCAST_MESSAGE, admin_broadcast_conv
from bot.handlers.onboarding import (
    SELECT_INTERESTS,
    SELECT_LANG,
    SELECT_OCCUPATION,
    onboarding_conv,
)


def make_user(uid=1):
    return User(id=uid, is_bot=False, first_name="Test")


def message_update(text, uid=1, entities=None):
    msg = Message(
        message_id=10, date=datetime.now(),
        chat=Chat(id=uid, type="private"), from_user=make_user(uid),
        text=text, entities=entities or [],
    )
    return Update(update_id=1, message=msg)


def callback_update(data, uid=1):
    msg = Message(
        message_id=20, date=datetime.now(),
        chat=Chat(id=uid, type="private"), from_user=make_user(uid),
    )
    cq = CallbackQuery(
        id="cb1", from_user=make_user(uid), chat_instance="ci", message=msg, data=data,
    )
    return Update(update_id=2, callback_query=cq)


def matches(handlers, update):
    return any(h.check_update(update) for h in handlers)


def test_admin_broadcast_entry_point():
    assert matches(admin_broadcast_conv.entry_points, callback_update("admin_broadcast"))
    assert not matches(admin_broadcast_conv.entry_points, callback_update("admin_stats"))


def test_admin_broadcast_state_accepts_text():
    state_handlers = admin_broadcast_conv.states[BROADCAST_MESSAGE]
    assert matches(state_handlers, message_update("heres the broadcast text"))


def test_onboarding_entry_point_is_start_command():
    from telegram.ext import CommandHandler

    entry = onboarding_conv.entry_points[0]
    assert isinstance(entry, CommandHandler)
    assert "start" in entry.commands
    # a plain message without the command must not match
    assert not matches(onboarding_conv.entry_points, message_update("hello"))


def test_onboarding_state_flow():
    cases = [
        (SELECT_LANG, "lang_ru"),
        (SELECT_INTERESTS, "interest_business"),
        (SELECT_OCCUPATION, "occ_student"),
    ]
    for state, data in cases:
        assert matches(onboarding_conv.states[state], callback_update(data)), data

    # unrelated callbacks must not match any state
    for state in (SELECT_LANG, SELECT_INTERESTS, SELECT_OCCUPATION):
        assert not matches(onboarding_conv.states[state], callback_update("unrelated_x"))
