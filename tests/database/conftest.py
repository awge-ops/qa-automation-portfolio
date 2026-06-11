"""Database test fixtures — SQLite connection management."""

import sqlite3

import pytest

from framework import config


@pytest.fixture
def default_db():
    """Connection to the application's default SQLite database."""
    if not config.DEFAULT_DB_PATH:
        pytest.skip("DEFAULT_DB_PATH not configured")
    conn = sqlite3.connect(config.DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def questions_db():
    """Connection to the questions SQLite database."""
    if not config.QUESTIONS_DB_PATH:
        pytest.skip("QUESTIONS_DB_PATH not configured")
    conn = sqlite3.connect(config.QUESTIONS_DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
