"""Config must never fall back to well-known secrets."""
import config


def test_no_hardcoded_secret_defaults():
    assert config.JWT_SECRET != "speedload_secret_2026"
    assert config.ADMIN_PASSWORD != "speedload2026"


def test_cors_origins_are_explicit():
    assert isinstance(config.ADMIN_CORS_ORIGINS, list)
    assert config.ADMIN_CORS_ORIGINS, "CORS origins list must not be empty"
    assert "*" not in config.ADMIN_CORS_ORIGINS
