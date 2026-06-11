"""
Root conftest — shared fixtures available to all test modules.

Provides:
  - Configuration loading (students, lessons, questions from INI files)
  - Question bank fixture (data-driven test support)
  - Test data loaders
"""

import configparser

import pytest

from framework import config
from framework.helpers.text import normalize


# ---------------------------------------------------------------------------
# INI data loaders
# ---------------------------------------------------------------------------

def _load_ini(path, encoding="utf-8"):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read(path, encoding=encoding)
    return parser


@pytest.fixture(scope="session")
def students_config():
    return _load_ini(config.STUDENTS_INI)


@pytest.fixture(scope="session")
def lessons_config():
    return _load_ini(config.LESSONS_INI)


@pytest.fixture(scope="session")
def tests_config():
    return _load_ini(config.TESTS_INI)


@pytest.fixture(scope="session")
def questions_config():
    return _load_ini(config.QUESTIONS_INI)


@pytest.fixture(scope="session")
def question_bank(questions_config) -> dict[str, dict[str, str]]:
    """
    Load all questions keyed by reference number.

    Returns: {reference: {question_text, correct_answer, section}}
    """
    bank: dict[str, dict[str, str]] = {}
    for section in questions_config.sections():
        reference = normalize(questions_config.get(section, "reference", fallback=""))
        if not reference:
            continue
        bank[reference] = {
            "section": section,
            "question_text": normalize(questions_config.get(section, "question_text", fallback="")),
            "correct_answer": normalize(questions_config.get(section, "correct_answer", fallback="")),
        }
    return bank


@pytest.fixture(scope="session")
def student_credentials(students_config):
    """Load credentials for a test student."""
    def _load(section: str = "new_student") -> dict[str, str]:
        return {
            "account_number": students_config[section]["account_number"],
            "licence_key": students_config[section]["licence_key"],
            "email": students_config[section].get("email", ""),
            "password": students_config[section].get("password", ""),
        }
    return _load


@pytest.fixture(scope="session")
def lesson_definition(lessons_config):
    """Load a lesson definition from config."""
    def _load(section: str = "smoke_test") -> dict[str, str]:
        return {
            "module": lessons_config[section]["module"],
            "id": lessons_config[section]["id"],
            "name": lessons_config[section]["name"],
            "pages": int(lessons_config[section]["pages"]),
        }
    return _load
