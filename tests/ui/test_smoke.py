"""
End-to-end smoke test — the full user journey from activation to data verification.

This is the primary CI test. It exercises:
  1. Admin portal: student creation
  2. Desktop app: activation → login → content download → lesson → quiz → sync
  3. Admin portal: data verification (tracking, test results, study time)

Tests are ordered and dependent — if activation fails, subsequent tests are skipped.
"""

import pytest

from framework import config
from tests.ui.pages import ActivationPage, DashboardPage, LessonPage, QuizPage
from tests.ui.pages.admin import AdminLoginPage, AdminStudentPage


@pytest.mark.smoke
@pytest.mark.ui
class TestSmokeE2E:
    """Full E2E smoke test — 13 sequential steps."""

    def test_01_admin_login(self, admin_login_page: AdminLoginPage):
        """Log into the admin portal as system admin."""
        admin_login_page.ensure_authenticated(config.ADMIN_URL)

    def test_02_create_student(self, admin_student_page: AdminStudentPage, students_config):
        """Create a new student account via the admin portal."""
        student = students_config["new_student"]
        admin_student_page.create_student(
            name=student["name"],
            email=student["email"],
            account_number=student["account_number"],
        )

    def test_03_activate(self, activation_page: ActivationPage, student_credentials):
        """Activate the desktop app with the new student's licence."""
        creds = student_credentials("new_student")
        activation_page.open()
        activation_page.activate(creds["account_number"], creds["licence_key"])

    def test_04_initial_update(self, dashboard_page: DashboardPage):
        """Handle the initial application update after first activation."""
        dashboard_page.page.wait_for_url(
            f"{config.APP_ADDRESS}/checking-updates",
            timeout=120_000,
        )

    def test_05_first_login(self, app_page, student_credentials):
        """Log into the app with student credentials."""
        from tests.ui.pages.activation_page import LoginPage
        creds = student_credentials("new_student")
        login = LoginPage(app_page)
        login.login(creds["email"], creds["password"])
        login.expect_dashboard_redirect()

    def test_06_download_updates(self, dashboard_page: DashboardPage):
        """Download all available content updates."""
        dashboard_page.wait_for_loaded()
        dashboard_page.wait_for_updates_status()

    def test_07_open_lesson(
        self,
        dashboard_page: DashboardPage,
        lesson_page: LessonPage,
        lesson_definition,
    ):
        """Open a lesson, navigate through it, and trigger the exit modal."""
        lesson = lesson_definition("smoke_test")
        dashboard_page.select_module(lesson["module"])
        dashboard_page.wait_for_lesson_visible(lesson["id"])
        dashboard_page.open_lesson(lesson["id"])

        lesson_page.click_through_and_exit(lesson["name"], lesson["pages"])

    def test_08_take_quiz(self, quiz_page: QuizPage, question_bank, tests_config):
        """Complete the lesson quiz with correct answers."""
        question_count = int(tests_config["smoke_test"]["questions"])

        quiz_page.page.locator(LessonPage.TAKE_QUIZ_LINK).click()
        quiz_page.expect_url(QuizPage.QUESTION_URL_RE, timeout=30_000)

        answered = quiz_page.answer_all_questions(question_count, question_bank)
        assert len(answered) == question_count

    def test_09_verify_quiz_results(self, quiz_page: QuizPage):
        """Verify 100% pass on the results screen."""
        quiz_page.verify_results("100%")
        quiz_page.return_to_dashboard()

    def test_10_sync(self, dashboard_page: DashboardPage):
        """Trigger sync and wait for completion."""
        dashboard_page.ensure_on_dashboard()
        dashboard_page.click_sync()
        dashboard_page.wait_for_sync_complete()

    def test_11_verify_tracking_data(self, admin_page, student_credentials):
        """Verify lesson tracking data appeared in the admin portal."""
        from tests.ui.pages.admin import AdminStudentPage
        admin = AdminStudentPage(admin_page)
        details = admin.read_student_details()
        assert details, "No student details found in admin portal"

    def test_12_verify_test_data(self, admin_page):
        """Verify quiz results appeared in the admin portal."""
        from tests.ui.pages.admin import AdminStudentPage
        admin = AdminStudentPage(admin_page)
        results = admin.read_test_results()
        assert len(results) > 0, "No test results found in admin portal"

    def test_13_verify_study_time(self, admin_page):
        """Verify study time was recorded in the admin portal."""
        from tests.ui.pages.admin import AdminStudentPage
        admin = AdminStudentPage(admin_page)
        entries = admin.read_study_time_entries()
        assert len(entries) > 0, "No study time entries found in admin portal"
