"""Pytest configuration for the SpeedLoad test suite.

Sets a throwaway SQLite database as DATABASE_URL *before* any project module
is imported, so modules that create their engine at import time
(`database.connection`) get a working database. Tests that need an isolated
database create their own engines on top of this.
"""
import os
import tempfile

_TEST_DIR = tempfile.mkdtemp(prefix="speedload_tests_")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DIR}/test.db"
