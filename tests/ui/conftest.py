"""
UI test fixtures — browser lifecycle and page object creation.

Supports two modes:
  - CDP connection to a running desktop app (production)
  - Fresh browser launch (local development / CI)
"""

import os
import uuid

import pytest
from playwright.sync_api import sync_playwright

from framework import config
from framework.browser import connect_or_launch, get_or_open_app_page
from tests.ui.pages import ActivationPage, DashboardPage, LessonPage, QuizPage
from tests.ui.pages.admin import AdminLoginPage, AdminQuestionsPage, AdminStudentPage


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def app_browser(playwright_instance):
    """Connect to the desktop app browser via CDP or launch a new one."""
    browser, owns = connect_or_launch(
        playwright_instance,
        debug_host=config.DEBUG_HOST,
        debug_port=config.DEBUG_PORT,
        headless=config.HEADLESS,
        session_name="app",
    )
    yield browser
    if owns:
        browser.close()


@pytest.fixture(scope="session")
def admin_browser(playwright_instance):
    """Browser for admin portal tests — always launches fresh."""
    browser = playwright_instance.chromium.launch(headless=config.HEADLESS)
    yield browser
    browser.close()


@pytest.fixture
def app_context(app_browser):
    """Fresh browser context with HAR recording for each test."""
    job_id = str(uuid.uuid4())
    har_path = os.path.join(config.EXPORT_PATH, f"{job_id}-app.har")
    os.makedirs(config.EXPORT_PATH, exist_ok=True)
    context = app_browser.new_context(record_har_path=har_path, record_har_mode="full")
    yield context
    context.close()


@pytest.fixture
def admin_context(admin_browser):
    """Fresh browser context for admin portal tests."""
    job_id = str(uuid.uuid4())
    har_path = os.path.join(config.EXPORT_PATH, f"{job_id}-admin.har")
    os.makedirs(config.EXPORT_PATH, exist_ok=True)
    context = admin_browser.new_context(record_har_path=har_path, record_har_mode="full")
    yield context
    context.close()


@pytest.fixture
def app_page(app_context):
    return app_context.new_page()


@pytest.fixture
def admin_page(admin_context):
    return admin_context.new_page()


# ---------------------------------------------------------------------------
# Page object fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def activation_page(app_page) -> ActivationPage:
    return ActivationPage(app_page)


@pytest.fixture
def dashboard_page(app_page) -> DashboardPage:
    return DashboardPage(app_page)


@pytest.fixture
def lesson_page(app_page) -> LessonPage:
    return LessonPage(app_page)


@pytest.fixture
def quiz_page(app_page) -> QuizPage:
    return QuizPage(app_page)


@pytest.fixture
def admin_login_page(admin_page) -> AdminLoginPage:
    return AdminLoginPage(admin_page)


@pytest.fixture
def admin_questions_page(admin_page) -> AdminQuestionsPage:
    return AdminQuestionsPage(admin_page)


@pytest.fixture
def admin_student_page(admin_page) -> AdminStudentPage:
    return AdminStudentPage(admin_page)
