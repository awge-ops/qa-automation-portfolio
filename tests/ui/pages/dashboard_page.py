"""Page object for the main application dashboard."""

from __future__ import annotations

import re

from playwright.sync_api import expect

from framework import config
from tests.ui.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Main dashboard — module selection, lesson list, sync, updates."""

    MODULE_SELECTOR = "select.module-selector"
    GRAPHS_CONTAINER = "main .col-lg-14 .card, main [class*='chart']"
    SYLLABUS_CONTAINER = "main .col-lg-10 .card, main [class*='syllabus']"

    SYNC_TEXT_PATTERN = re.compile(r"Click to sync|Progress last saved", re.IGNORECASE)
    UPDATE_TEXT_PATTERN = re.compile(r"New content available|Up to date", re.IGNORECASE)
    DASHBOARD_TITLE_PATTERN = re.compile(r"\bMy Progress\b", re.IGNORECASE)

    def open(self) -> None:
        self.navigate("dashboard")
        self.wait_for_loaded()

    def wait_for_loaded(self, timeout: int = 60_000) -> None:
        """Wait until the dashboard is fully rendered with all key elements."""
        self.wait_for_text(self.DASHBOARD_TITLE_PATTERN, timeout=timeout)
        self.expect_url(f"{config.APP_ADDRESS}/dashboard", timeout=timeout)

    def ensure_on_dashboard(self) -> None:
        if "/dashboard" not in (self.page.url or ""):
            self.open()

    def select_module(self, module_name: str, timeout: int = 30_000) -> None:
        self.page.select_option(self.MODULE_SELECTOR, label=module_name)

    def wait_for_lesson_visible(self, lesson_id: str, timeout: int = 30_000) -> None:
        selector = self._lesson_selector(lesson_id)
        self.page.locator(selector).wait_for(state="visible", timeout=timeout)

    def open_lesson(self, lesson_id: str, timeout: int = 30_000) -> None:
        selector = self._lesson_selector(lesson_id)
        self.page.locator(selector).click()
        self.expect_url(f"{config.APP_ADDRESS}/lesson/{lesson_id}", timeout=timeout)

    def click_sync(self) -> None:
        self.page.get_by_text(self.SYNC_TEXT_PATTERN).first.click()

    def wait_for_sync_complete(self, timeout: int = 60_000) -> None:
        self.page.get_by_text(re.compile(r"Progress last saved", re.IGNORECASE)).first.wait_for(
            state="visible", timeout=timeout
        )

    def wait_for_updates_status(self, timeout: int = 60_000) -> None:
        self.page.get_by_text(self.UPDATE_TEXT_PATTERN).first.wait_for(state="visible", timeout=timeout)

    @staticmethod
    def _lesson_selector(lesson_id: str) -> str:
        if len(lesson_id) > 1:
            return f"#\\3{lesson_id[0]} {lesson_id[1:]}"
        return f"#\\3{lesson_id}"
