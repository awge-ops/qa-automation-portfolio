"""Page object for the lesson viewer."""

from __future__ import annotations

from playwright.sync_api import expect

from framework import config
from tests.ui.pages.base_page import BasePage


class LessonPage(BasePage):
    """Lesson viewer — navigation, page content, exit modal."""

    LESSON_TITLE = "#lesson-title"
    HEADER_TITLE = "#lessonview h1"
    CONTENT_AREA = "#lessonview > div:nth-child(3) > div"
    NEXT_BUTTON = "button.next.btn-nav"
    PAGE_NAVIGATION = "#page-navigation"
    CLOSE_BUTTON = "#lessonview > div:nth-child(3) > button"
    EXIT_MODAL = "#finish-lesson .modal-dialog"
    TAKE_QUIZ_LINK = "#finish-lesson a:has-text('Take Quiz'), #finish-lesson a:nth-child(3)"

    def verify_title(self, expected_name: str) -> None:
        expect(self.page.locator(self.LESSON_TITLE)).to_contain_text(expected_name)

    def enter_lesson(self) -> None:
        """Click 'Next' from the title screen into the lesson content."""
        self.page.locator(self.NEXT_BUTTON).click()

    def verify_header(self, expected_name: str) -> None:
        expect(self.page.locator(self.HEADER_TITLE)).to_contain_text(expected_name)

    def get_page_content(self) -> str:
        return self.page.locator(self.CONTENT_AREA).text_content()

    def navigate_to_page(self, page_number: int) -> None:
        """Open the page navigation overlay and click a specific page."""
        self.page.locator(self.PAGE_NAVIGATION).click()
        page_button = (
            f"#lessonview .header-bar .page-navigation button:nth-child({page_number})"
        )
        self.page.locator(page_button).click()

    def wait_for_content_change(self, previous_content: str, timeout: int = 30_000) -> None:
        expect(self.page.locator(self.CONTENT_AREA)).not_to_have_text(
            previous_content, timeout=timeout
        )

    def close_lesson(self) -> None:
        """Click the close button and wait for the exit modal."""
        self.page.locator(self.CLOSE_BUTTON).click()
        self.page.locator(self.EXIT_MODAL).wait_for(state="visible")

    def click_take_quiz(self) -> None:
        self.page.locator(self.TAKE_QUIZ_LINK).click()
        self.expect_url(f"{config.APP_ADDRESS}/test/current", timeout=30_000)

    def click_through_and_exit(self, lesson_name: str, total_pages: int) -> None:
        """Full lesson walkthrough: enter, navigate to last page, close."""
        self.verify_title(lesson_name)
        self.enter_lesson()
        self.verify_header(lesson_name)

        first_page_content = self.get_page_content()
        self.navigate_to_page(total_pages)
        self.wait_for_content_change(first_page_content)
        self.close_lesson()
