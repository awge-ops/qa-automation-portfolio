"""Page object for admin student management."""

from __future__ import annotations

from framework import config
from framework.helpers.text import normalize
from tests.ui.pages.base_page import BasePage


class AdminStudentPage(BasePage):
    """Admin portal student creation, editing, and data verification."""

    STUDENT_NAME_INPUT = "#student-name, input[name='name']"
    STUDENT_EMAIL_INPUT = "#student-email, input[name='email']"
    ACCOUNT_NUMBER_INPUT = "#account-number, input[name='account_number']"
    SAVE_BUTTON = "button[type='submit']:has-text('Save'), input[type='submit']"

    STUDENT_DETAILS_TABLE = "table.student-details, .student-info table"
    TEST_RESULTS_TABLE = "table.test-results, [class*='test-result'] table"
    STUDY_TIME_TABLE = "table.study-time, [class*='study-time'] table"

    def create_student(self, name: str, email: str, account_number: str) -> None:
        self.page.locator(self.STUDENT_NAME_INPUT).first.fill(name)
        self.page.locator(self.STUDENT_EMAIL_INPUT).first.fill(email)
        self.page.locator(self.ACCOUNT_NUMBER_INPUT).first.fill(account_number)
        self.page.locator(self.SAVE_BUTTON).first.click()

    def read_student_details(self) -> dict[str, str]:
        """Read all key-value pairs from the student details table."""
        table = self.page.locator(self.STUDENT_DETAILS_TABLE).first
        table.wait_for(state="visible", timeout=10_000)
        rows = table.locator("tr")
        details = {}
        for i in range(rows.count()):
            cells = rows.nth(i).locator("td, th")
            if cells.count() >= 2:
                key = normalize(cells.nth(0).text_content())
                value = normalize(cells.nth(1).text_content())
                details[key] = value
        return details

    def read_test_results(self) -> list[dict[str, str]]:
        """Read test result rows from the student's test data table."""
        table = self.page.locator(self.TEST_RESULTS_TABLE).first
        table.wait_for(state="visible", timeout=10_000)
        return self._read_table_rows(table)

    def read_study_time_entries(self) -> list[dict[str, str]]:
        """Read study time entries from the student's study time table."""
        table = self.page.locator(self.STUDY_TIME_TABLE).first
        table.wait_for(state="visible", timeout=10_000)
        return self._read_table_rows(table)

    @staticmethod
    def _read_table_rows(table) -> list[dict[str, str]]:
        headers_row = table.locator("thead tr, tr:first-child")
        header_cells = headers_row.first.locator("th, td")
        headers = [normalize(header_cells.nth(i).text_content()) for i in range(header_cells.count())]

        body_rows = table.locator("tbody tr, tr:not(:first-child)")
        results = []
        for i in range(body_rows.count()):
            cells = body_rows.nth(i).locator("td")
            row_data = {}
            for j in range(min(cells.count(), len(headers))):
                row_data[headers[j]] = normalize(cells.nth(j).text_content())
            results.append(row_data)
        return results
