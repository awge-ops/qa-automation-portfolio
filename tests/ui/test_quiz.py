"""
Quiz and test-taking tests.

Covers:
  - Answering questions from the question bank (data-driven)
  - Results verification
  - Navigation back to dashboard after quiz
"""

import pytest

from tests.ui.pages import QuizPage


@pytest.mark.ui
class TestQuiz:

    @pytest.mark.parametrize("test_section", ["smoke_test"])
    def test_answer_all_questions(
        self,
        quiz_page: QuizPage,
        question_bank,
        tests_config,
        test_section: str,
    ):
        """All questions should be answerable using the configured question bank."""
        question_count = int(tests_config[test_section]["questions"])
        answered = quiz_page.answer_all_questions(question_count, question_bank)
        assert len(answered) == question_count

    def test_quiz_results_show_100_percent(self, quiz_page: QuizPage):
        """After answering all questions correctly, results should show 100%."""
        quiz_page.verify_results("100%")

    def test_return_to_dashboard_after_quiz(self, quiz_page: QuizPage):
        """Should be able to navigate back to dashboard from results page."""
        quiz_page.return_to_dashboard()
        quiz_page.expect_url(QuizPage.RESULTS_URL_RE.pattern.replace("/results", "").rstrip("$"))


@pytest.mark.ui
class TestProgressTest:
    """Progress test — a longer assessment with configurable question sets."""

    @pytest.mark.parametrize("section", ["initial_attempt"])
    @pytest.mark.slow
    def test_take_progress_test(
        self,
        dashboard_page,
        quiz_page: QuizPage,
        question_bank,
        tests_config,
        section: str,
    ):
        """Complete a progress test using configured answers."""
        question_count = int(tests_config[section]["questions"])
        answered = quiz_page.answer_all_questions(question_count, question_bank)
        assert len(answered) == question_count
        quiz_page.verify_results("100%")
        quiz_page.return_to_dashboard()
