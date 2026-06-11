"""Page object for the admin portal login flow."""

from __future__ import annotations

import time

from framework import config
from framework.browser import first_visible
from tests.ui.pages.base_page import BasePage


class AdminLoginPage(BasePage):
    """Handles admin portal authentication with multiple selector strategies."""

    USER_SELECTORS = ["#username", "input[name='username']", "input[type='email']"]
    PASSWORD_SELECTORS = ["#password", "input[name='password']", "input[type='password']"]
    SUBMIT_SELECTORS = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Login')",
        "button:has-text('Sign in')",
    ]

    ERROR_SELECTORS = [
        ".alert", ".alert-danger", ".error-summary",
        ".invalid-feedback", ".help-block-error", "[role='alert']",
    ]

    ERROR_MARKERS = (
        "invalid", "incorrect", "required", "failed",
        "error", "denied", "unauthor", "problem", "try again",
    )

    def is_login_page(self) -> bool:
        if "/login" in (self.page.url or "").lower():
            return True
        user = first_visible(self.page, self.USER_SELECTORS, timeout=600)
        password = first_visible(self.page, self.PASSWORD_SELECTORS, timeout=600)
        return user is not None and password is not None

    def login(self, username: str, password: str) -> None:
        user_field = first_visible(self.page, self.USER_SELECTORS, timeout=5_000)
        pass_field = first_visible(self.page, self.PASSWORD_SELECTORS, timeout=5_000)

        if user_field is None or pass_field is None:
            raise AssertionError("Login page detected but username/password inputs not found")

        user_field.fill(username)
        pass_field.fill(password)

        submitted = False
        for selector in self.SUBMIT_SELECTORS:
            try:
                self.page.locator(selector).first.click(timeout=2_000)
                submitted = True
                break
            except Exception:
                continue

        if not submitted:
            pass_field.press("Enter")

        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=10_000)
        except Exception:
            pass

    def ensure_authenticated(self, target_url: str) -> None:
        """Navigate to target URL, logging in if needed."""
        self.page.goto(target_url, wait_until="domcontentloaded", timeout=30_000)

        if not self.is_login_page():
            return

        username, password = config.ADMIN_USERNAME, config.ADMIN_PASSWORD
        if not username or not password:
            raise AssertionError("Login required but no admin credentials configured")

        self.login(username, password)
        self._wait_for_login_resolution()
        self.page.goto(target_url, wait_until="domcontentloaded", timeout=30_000)

    def _wait_for_login_resolution(self, timeout_ms: int = 15_000) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            if not self.is_login_page():
                return
            if self._has_auth_error():
                raise AssertionError(f"Login failed. URL: {self.page.url}, errors: {self._visible_errors()}")
            self.page.wait_for_timeout(250)

        if self.is_login_page():
            raise AssertionError(f"Login form still visible after submit. URL: {self.page.url}")

    def _has_auth_error(self) -> bool:
        for msg in self._visible_errors():
            if any(marker in msg.lower() for marker in self.ERROR_MARKERS):
                return True
        return False

    def _visible_errors(self) -> list[str]:
        messages = []
        for selector in self.ERROR_SELECTORS:
            locator = self.page.locator(selector)
            try:
                for i in range(min(locator.count(), 5)):
                    text = locator.nth(i).inner_text(timeout=500).strip()
                    if text:
                        messages.append(text)
            except Exception:
                continue
        return messages
