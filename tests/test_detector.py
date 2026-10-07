"""Unit tests for platform detection (downloader/detector.py)."""
import pytest

from downloader.detector import detect_platform


@pytest.mark.parametrize("url,expected", [
    ("https://www.youtube.com/watch?v=abc123", "youtube"),
    ("https://youtu.be/abc123", "youtube"),
    ("youtube.com/watch?v=abc", "youtube"),
    ("https://www.instagram.com/reel/xyz789/", "instagram"),
    ("https://instagram.com/p/abc123", "instagram"),
    ("https://www.instagram.com/tv/xyz", "instagram"),
    ("https://www.tiktok.com/@user/video/123456", "tiktok"),
    ("https://vt.tiktok.com/Zabc/", "tiktok"),
    ("https://twitter.com/user/status/123456789", "twitter"),
    ("https://x.com/user/status/123456789", "twitter"),
    ("https://www.facebook.com/watch/?v=123456", "facebook"),
    ("https://www.pinterest.com/pin/123456/", "pinterest"),
    ("https://example.com/video", "other"),
    ("https://vimeo.com/12345", "other"),
    ("not a url at all", "other"),
    ("", "other"),
])
def test_detect_platform(url, expected):
    assert detect_platform(url) == expected
