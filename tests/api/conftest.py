"""API test fixtures — admin portal data verification via browser."""

import pytest
from playwright.sync_api import sync_playwright

from framework import config
from tests.ui.pages.admin import AdminLoginPage, AdminStudentPage


@pytest.fixture(scope="module")
def admin_session():
    """Authenticated admin portal session for data verification."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=config.HEADLESS)
        context = browser.new_context()
        page = context.new_page()

        login = AdminLoginPage(page)
        login.ensure_authenticated(config.ADMIN_URL)

        yield page

        context.close()
        browser.close()
