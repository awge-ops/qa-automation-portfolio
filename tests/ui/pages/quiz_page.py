"""Page object for the quiz / test-taking flow."""

from __future__ import annotations

import re

from playwright.sync_api import expect

from framework import config
from framework.browser import first_visible
from framework.helpers.text import normalize
from tests.ui.pages.base_page import BasePage


class QuizPage(BasePage):
    """Quiz flow — answering questions, navigating, and verifying results."""

    REFERENCE_LOCATOR = "main .question-heading .reference"
    QUESTION_TEXT = "main .question p"
    ANSWERS_CONTAINER = "main .answers"
    NEXT_BUTTON = "button.next.btn-nav"
    FINISH_CONFIRM_BUTTON = "#confirm-finished .modal-footer a:first-child"
    FINISH_MODAL = "#confirm-finished .modal-dialog"

    RESULTS_STATUS = ".results-header .result-status"
    RESULTS_PERCENTAGE = ".results-header .percentage"
    BACK_TO_DASHBOARD = "main button:has-text('Back'), main a:has-text('Dashboard')"

    QUESTION_URL_RE = re.compile(rf"^{re.escape(config.APP_ADDRESS)}/test/current(?:[/?#].*)?$")
    RESULTS_URL_RE = re.compile(rf"^{re.escape(config.APP_ADDRESS)}/test/current/results(?:[/?#].*)?$")
    REFERENCE_RE = re.compile(r"Ref:\s*([0-9]+)", re.IGNORECASE)

    def read_current_reference(self) -> str:
        """Extract the question reference number from the heading."""
        heading = self.page.locator(self.REFERENCE_LOCATOR).first
        heading.wait_for(state="visible", timeout=10_000)
        text = normalize(heading.text_content())
        match = self.REFERENCE_RE.search(text)
        if not match:
            # Fallback: strip "Ref: " prefix
            return text.replace("Ref:", "").strip()
        return match.group(1)

    def verify_question_text(self, expected: str) -> None:
        if not expected:
            return
        expect(self.page.locator(self.QUESTION_TEXT).first).to_contain_text(expected, timeout=10_000)

    def select_answer(self, correct_answer: str) -> None:
        """Find and click the correct answer from the answer options."""
        answers = self.page.locator(self.ANSWERS_CONTAINER).first
        answers.wait_for(state="visible", timeout=5_000)

        # Try exact text match first, then normalized
        for text_match in [correct_answer, normalize(correct_answer)]:
            candidate = answers.get_by_text(text_match, exact=True).first
            try:
                candidate.wait_for(state="visible", timeout=2_000)
                candidate.click(timeout=5_000)
                return
            except Exception:
                continue

        # Fallback: iterate visible answer divs
        answer_divs = answers.locator("div > span")
        for i in range(answer_divs.count()):
            span = answer_divs.nth(i)
            if normalize(span.text_content()) == normalize(correct_answer):
                span.click()
                return

        visible = answers.evaluate(
            """(el) => [...el.querySelectorAll("span")]
                .map(n => n.textContent.trim())
                .filter(Boolean).slice(0, 8)"""
        )
        raise AssertionError(
            f"Could not find answer {correct_answer!r}. Visible: {visible!r}"
        )

    def click_next(self) -> None:
        next_btn = self.page.locator(self.NEXT_BUTTON).first
        expect(next_btn).to_be_enabled(timeout=10_000)
        next_btn.click()

    def wait_for_next_question(self, previous_reference: str) -> None:
        """Wait until the question reference changes (next question loaded)."""
        heading = self.page.locator(self.REFERENCE_LOCATOR).first
        expect(heading).not_to_contain_text(previous_reference, timeout=10_000)

    def wait_for_finish_modal(self) -> None:
        self.page.locator(self.FINISH_MODAL).wait_for(state="visible", timeout=10_000)

    def confirm_finish(self) -> None:
        self.page.locator(self.FINISH_CONFIRM_BUTTON).click()

    def verify_results(self, expected_percentage: str = "100%") -> None:
        expect(self.page).to_have_url(self.RESULTS_URL_RE, timeout=30_000)

        result_marker = self.find_first_visible(
            [self.RESULTS_STATUS, self.RESULTS_PERCENTAGE], timeout=10_000
        )
        assert result_marker is not None, "Result marker not visible on results page"

        self.page.get_by_text(re.compile(rf"\b{re.escape(expected_percentage)}\b")).first.wait_for(
            state="visible", timeout=10_000
        )

    def return_to_dashboard(self) -> None:
        btn = self.find_first_visible([self.BACK_TO_DASHBOARD], timeout=5_000)
        if btn:
            btn.click()
        else:
            self.navigate("dashboard")

    def answer_all_questions(
        self,
        question_count: int,
        question_bank: dict[str, dict[str, str]],
    ) -> list[str]:
        """
        Answer all quiz questions using the provided question bank.

        Args:
            question_count: Total number of questions in this quiz.
            question_bank: Mapping of reference -> {question_text, correct_answer}.

        Returns:
            List of answered question references.
        """
        answered: list[str] = []

        for i in range(1, question_count + 1):
            reference = self.read_current_reference()
            definition = question_bank.get(reference)
            assert definition is not None, (
                f"Reference {reference!r} not found in question bank"
            )

            self.verify_question_text(definition.get("question_text", ""))
            self.select_answer(definition["correct_answer"])
            answered.append(reference)

            self.click_next()

            if i < question_count:
                self.wait_for_next_question(reference)
            else:
                self.wait_for_finish_modal()
                self.confirm_finish()

        return answered
