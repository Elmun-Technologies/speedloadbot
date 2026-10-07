"""Config must never fall back to well-known secrets."""
import config


def test_no_hardcoded_secret_defaults():
    assert config.JWT_SECRET != "speedload_secret_2026"
    assert config.ADMIN_PASSWORD != "speedload2026"


def test_cors_origins_are_explicit():
    assert isinstance(config.ADMIN_CORS_ORIGINS, list)
    assert config.ADMIN_CORS_ORIGINS, "CORS origins list must not be empty"
    assert "*" not in config.ADMIN_CORS_ORIGINS


def test_admin_ids_empty_by_default():
    """Admin bot commands stay disabled until ADMIN_IDS is configured."""
    assert config.ADMIN_IDS == []


def test_admin_ids_parsed_from_env(monkeypatch):
    """ADMIN_IDS is a comma-separated list of Telegram user IDs from the env."""
    import importlib

    monkeypatch.setenv("ADMIN_IDS", "123456789, 987654321 ,not-a-number")
    importlib.reload(config)
    try:
        assert config.ADMIN_IDS == [123456789, 987654321]
    finally:
        monkeypatch.delenv("ADMIN_IDS")
        importlib.reload(config)
