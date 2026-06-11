"""
Admin portal question type verification tests.

Verifies that each question type in the admin portal displays correctly:
  - Reference filter returns the expected question
  - Question type matches the expected internal type
  - Resource images are present where expected (annexes, answer images)
"""

import pytest
from urllib.parse import urljoin

from framework import config
from tests.ui.pages.admin import AdminLoginPage, AdminQuestionsPage


EXPECTED_INTERNAL_TYPES = {
    "multi_select": {"multiple_select"},
    "question_annex": {"multiple_choice", "question_annex"},
    "answer_image": {"multiple_choice"},
    "multiple_question_annexes": {"multiple_choice"},
    "multiple_answer_images": {"multiple_select"},
    "new_question": {"multiple_choice"},
}


@pytest.fixture
def authenticated_questions_page(admin_page) -> AdminQuestionsPage:
    """Admin questions page with authentication handled."""
    login = AdminLoginPage(admin_page)
    login.ensure_authenticated(config.ADMIN_QUESTIONS_URL)
    return AdminQuestionsPage(admin_page)


@pytest.mark.admin
@pytest.mark.ui
class TestAdminQuestionTypes:

    @pytest.mark.parametrize("question_section", [
        "multi_select",
        "question_annex",
        "answer_image",
        "multiple_question_annexes",
        "multiple_answer_images",
        "new_question",
    ])
    def test_question_type_matches_config(
        self,
        authenticated_questions_page: AdminQuestionsPage,
        questions_config,
        question_section: str,
    ):
        """Each question type should be correctly classified in the admin portal."""
        section = questions_config[question_section]
        question = {
            "id": section.get("id", "").strip(),
            "reference": section.get("reference", "").strip(),
            "question_text": section.get("question_text", "").strip(),
        }

        page = authenticated_questions_page
        page.open()
        count = page.filter_by_reference(question["reference"])
        assert count >= 1, f"No results for reference {question['reference']!r}"

        href, strategy = page.find_edit_link(question)
        target_url = urljoin(config.ADMIN_QUESTIONS_URL, href)
        page.page.goto(target_url, wait_until="domcontentloaded", timeout=30_000)

        expected_types = EXPECTED_INTERNAL_TYPES.get(question_section, {question_section})
        page.verify_question_type(expected_types)

    @pytest.mark.parametrize("question_section,min_resources", [
        ("question_annex", 1),
        ("answer_image", 1),
        ("multiple_question_annexes", 2),
        ("multiple_answer_images", 2),
    ])
    def test_resource_images_present(
        self,
        authenticated_questions_page: AdminQuestionsPage,
        questions_config,
        question_section: str,
        min_resources: int,
    ):
        """Questions with annexes/images should have the expected number of resources."""
        section = questions_config[question_section]
        question = {
            "id": section.get("id", "").strip(),
            "reference": section.get("reference", "").strip(),
            "question_text": section.get("question_text", "").strip(),
        }

        page = authenticated_questions_page
        page.open()
        page.filter_by_reference(question["reference"])
        href, _ = page.find_edit_link(question)
        target_url = urljoin(config.ADMIN_QUESTIONS_URL, href)
        page.page.goto(target_url, wait_until="domcontentloaded", timeout=30_000)

        actual = page.count_resource_images()
        assert actual >= min_resources, (
            f"Expected at least {min_resources} resource images for {question_section}, got {actual}"
        )
