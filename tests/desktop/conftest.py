"""Desktop test fixtures — Windows client and paths."""

import logging

import pytest

from framework import config


@pytest.fixture(scope="module")
def windows_client():
    """Windows command execution client (skips on non-Windows)."""
    try:
        from framework.windows.client import WindowsClient
        logger = logging.getLogger("desktop_tests")
        return WindowsClient(logger=logger)
    except RuntimeError:
        pytest.skip("Desktop tests require Windows")
