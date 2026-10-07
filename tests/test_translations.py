"""All languages must define the same keys — including the ones handlers use."""
from utils.translations import TEXTS

REQUIRED_KEYS = [
    "welcome_new", "welcome_returning", "loading", "unsupported", "too_large",
    "private", "generic_error", "moral_warning", "referral", "account",
    "btn_donate", "donate_text", "btn_download", "btn_account", "btn_referral",
    "btn_language", "btn_help", "btn_creators", "btn_leaderboard",
    "choose_platform", "send_link_prompt", "help_text", "btn_tickets",
    "btn_support", "ticket_prompt", "ticket_thanks", "creator_title",
    "tool_descriptions", "btn_v2script", "btn_cleanmeta", "btn_compress",
    "btn_thumbnail", "btn_trendradar", "btn_longtoshort", "btn_buy_credits",
    "creator_credits_info", "no_credits_error", "btn_back",
    "onboarding_interests", "onboarding_occupation", "onboarding_thanks",
    "interest_ent", "interest_biz", "interest_edu", "interest_tech",
    "occ_creator", "occ_student", "occ_pro", "occ_other",
    "status_processing", "status_compressing", "status_transcribing",
    "status_uploading", "status_done", "status_error", "status_main_menu",
    "status_send_file", "status_too_long", "quality_audio", "quality_thumbnail",
    # used by handlers, previously missing entirely:
    "language_updated", "what_to_download", "banned",
]

LANGS = ("uz", "ru", "en")


def test_all_languages_present():
    for lang in LANGS:
        assert lang in TEXTS, f"Missing language block: {lang}"


def test_all_languages_define_required_keys():
    for lang in LANGS:
        missing = [k for k in REQUIRED_KEYS if k not in TEXTS[lang]]
        assert not missing, f"{lang} is missing keys: {missing}"


def test_all_languages_have_identical_keys():
    uz_keys = set(TEXTS["uz"].keys())
    for lang in ("ru", "en"):
        assert set(TEXTS[lang].keys()) == uz_keys, (
            f"{lang} keys differ from uz: "
            f"missing={uz_keys - set(TEXTS[lang].keys())}, "
            f"extra={set(TEXTS[lang].keys()) - uz_keys}"
        )
