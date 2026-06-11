"""
Base page object with common interactions and assertions.

All page objects inherit from this class. It provides:
  - Screenshot capture
  - Visible element waiting
  - Common navigation patterns
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect

from framework import config
from framework.browser import first_visible

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def navigate(self, path: str, timeout: int = 30_000) -> None:
        url = f"{config.APP_ADDRESS}/{path.lstrip('/')}"
        self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)

    def expect_url(self, pattern: str | re.Pattern, timeout: int = 30_000) -> None:
        expect(self.page).to_have_url(pattern, timeout=timeout)

    def screenshot(self, export_dir: str, name: str) -> str | None:
        path = os.path.join(export_dir, f"{name}-screenshot.png")
        try:
            self.page.screenshot(path=path, full_page=True)
            return path
        except Exception:
            return None

    def find_first_visible(self, selectors: list[str], timeout: int = 3_000) -> Locator | None:
        return first_visible(self.page, selectors, timeout=timeout)

    def wait_for_text(self, text: str | re.Pattern, timeout: int = 10_000) -> Locator:
        locator = self.page.get_by_text(text).first
        locator.wait_for(state="visible", timeout=timeout)
        return locator
