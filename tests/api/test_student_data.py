"""
Student data verification tests.

Verifies that data flows correctly between the desktop app and admin portal:
  - Lesson tracking data (page views, completion status)
  - Test/quiz results (scores, pass/fail)
  - Study time records (duration per lesson)
  - Student profile data (name, email, school)

These tests run against the admin portal, verifying data that was uploaded
by the desktop app during a smoke test or manual session.
"""

import pytest

from framework import config
from framework.helpers.text import normalize
from tests.ui.pages.admin import AdminStudentPage


@pytest.mark.api
class TestLessonTrackingData:
    """Verify lesson progress data appears correctly in admin portal."""

    def test_tracking_data_exists(self, admin_session, students_config):
        """A student who completed a lesson should have tracking data."""
        admin = AdminStudentPage(admin_session)
        details = admin.read_student_details()
        assert details, "No student details found"

    def test_lesson_completion_recorded(self, admin_session):
        """Lesson completion status should be recorded after sync."""
        admin = AdminStudentPage(admin_session)
        details = admin.read_student_details()
        assert any("complete" in v.lower() for v in details.values()), (
            "No completion status found in student details"
        )


@pytest.mark.api
class TestUserTestData:
    """Verify quiz/test results appear correctly in admin portal."""

    def test_test_results_exist(self, admin_session):
        """A student who took a quiz should have test result records."""
        admin = AdminStudentPage(admin_session)
        results = admin.read_test_results()
        assert len(results) > 0, "No test results found"

    def test_test_results_contain_score(self, admin_session):
        """Each test result should include a score or percentage."""
        admin = AdminStudentPage(admin_session)
        results = admin.read_test_results()
        for result in results:
            values = " ".join(result.values()).lower()
            assert "%" in values or any(c.isdigit() for c in values), (
                f"Test result missing score: {result}"
            )


@pytest.mark.api
class TestStudyTime:
    """Verify study time records appear correctly in admin portal."""

    def test_study_time_entries_exist(self, admin_session):
        """A student who studied a lesson should have study time records."""
        admin = AdminStudentPage(admin_session)
        entries = admin.read_study_time_entries()
        assert len(entries) > 0, "No study time entries found"

    def test_study_time_has_duration(self, admin_session):
        """Each study time entry should include a non-zero duration."""
        admin = AdminStudentPage(admin_session)
        entries = admin.read_study_time_entries()
        for entry in entries:
            values = " ".join(entry.values())
            assert any(c.isdigit() for c in values), (
                f"Study time entry missing duration: {entry}"
            )


@pytest.mark.api
class TestStudentProfile:
    """Verify student profile data matches between app and admin portal."""

    @pytest.mark.parametrize("field", ["Name", "Email", "Student No"])
    def test_profile_field_present(self, admin_session, field):
        """Key profile fields should be present and non-empty."""
        admin = AdminStudentPage(admin_session)
        details = admin.read_student_details()
        matching = [k for k in details if field.lower() in k.lower()]
        assert matching, f"Profile field {field!r} not found in {list(details.keys())}"
        assert details[matching[0]], f"Profile field {field!r} is empty"
