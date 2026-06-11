"""Page object for the application activation and login flow."""

from __future__ import annotations

from playwright.sync_api import expect

from framework import config
from tests.ui.pages.base_page import BasePage


class ActivationPage(BasePage):
    """Handles licence activation — entering account number and key."""

    ACCOUNT_INPUT = "#install_reference"
    LICENCE_INPUT = "#licence_key"
    ACTIVATE_BUTTON = "#activation-form button[type='submit']"

    def open(self, timeout: int = 120_000) -> None:
        self.page.goto(config.APP_ADDRESS, timeout=timeout)
        self.expect_url(f"{config.APP_ADDRESS}/activate")

    def activate(self, account_number: str, licence_key: str) -> None:
        self.page.locator(self.ACCOUNT_INPUT).fill(account_number)
        self.page.locator(self.LICENCE_INPUT).fill(licence_key)
        self.page.locator(self.ACTIVATE_BUTTON).click()
        self.expect_url(f"{config.APP_ADDRESS}/checking-updates", timeout=30_000)


class LoginPage(BasePage):
    """Handles student login after activation."""

    EMAIL_INPUT = "#email"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "button[type='submit']"

    def login(self, email: str, password: str) -> None:
        self.page.locator(self.EMAIL_INPUT).fill(email)
        self.page.locator(self.PASSWORD_INPUT).fill(password)
        self.page.locator(self.LOGIN_BUTTON).click()

    def expect_dashboard_redirect(self, timeout: int = 60_000) -> None:
        self.expect_url(f"{config.APP_ADDRESS}/dashboard", timeout=timeout)
