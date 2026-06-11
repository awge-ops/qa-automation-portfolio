"""
Lesson navigation and completion tests.

Covers:
  - Module selection and lesson visibility
  - Lesson content navigation (title, pages, exit modal)
  - Click-through to quiz
"""

import pytest

from tests.ui.pages import DashboardPage, LessonPage


@pytest.mark.ui
class TestLessonFlow:

    def test_select_module_shows_lesson(
        self,
        dashboard_page: DashboardPage,
        lesson_definition,
    ):
        """Selecting a module should make its lessons visible."""
        lesson = lesson_definition("smoke_test")
        dashboard_page.open()
        dashboard_page.select_module(lesson["module"])
        dashboard_page.wait_for_lesson_visible(lesson["id"])

    def test_open_lesson(
        self,
        dashboard_page: DashboardPage,
        lesson_page: LessonPage,
        lesson_definition,
    ):
        """Opening a lesson should navigate to the lesson URL."""
        lesson = lesson_definition("smoke_test")
        dashboard_page.open()
        dashboard_page.select_module(lesson["module"])
        dashboard_page.open_lesson(lesson["id"])
        lesson_page.verify_title(lesson["name"])

    def test_click_through_lesson(
        self,
        dashboard_page: DashboardPage,
        lesson_page: LessonPage,
        lesson_definition,
    ):
        """Navigating through all pages and closing should show the exit modal."""
        lesson = lesson_definition("smoke_test")
        dashboard_page.open()
        dashboard_page.select_module(lesson["module"])
        dashboard_page.open_lesson(lesson["id"])
        lesson_page.click_through_and_exit(lesson["name"], lesson["pages"])

    def test_exit_modal_offers_quiz(
        self,
        dashboard_page: DashboardPage,
        lesson_page: LessonPage,
        lesson_definition,
    ):
        """The exit modal should contain a 'Take Quiz' link."""
        lesson = lesson_definition("smoke_test")
        dashboard_page.open()
        dashboard_page.select_module(lesson["module"])
        dashboard_page.open_lesson(lesson["id"])
        lesson_page.click_through_and_exit(lesson["name"], lesson["pages"])

        quiz_link = lesson_page.page.locator(LessonPage.TAKE_QUIZ_LINK)
        assert quiz_link.is_visible(), "Take Quiz link not visible in exit modal"
