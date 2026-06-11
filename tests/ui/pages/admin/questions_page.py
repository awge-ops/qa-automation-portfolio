"""Page object for the admin portal question management page."""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from framework import config
from framework.browser import first_visible
from framework.helpers.text import canonical, normalize, snippet
from tests.ui.pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class AdminQuestionsPage(BasePage):
    """Admin question bank — filtering, searching, and verifying question data."""

    REFERENCE_INPUT_SELECTORS = [
        "#questionbank-q",
        "#question-reference",
        "input[name='q']",
        "input[name='question-reference']",
        "input[placeholder*='reference']",
        "input[placeholder*='Query or reference']",
    ]

    FILTER_BUTTON = "input.btn-primary[type=submit]"
    RESULT_COUNT = "div.records span.values"
    RESULT_ROW = "table tbody tr"
    EDIT_LINK = "a[href*='/admin/questions/edit/']"
    QUESTION_TYPE = "#question-type"
    RESOURCE_IMAGE = 'img[src*="/data/question/"]'

    def open(self) -> None:
        self.page.goto(config.ADMIN_QUESTIONS_URL, wait_until="domcontentloaded", timeout=30_000)

    def filter_by_reference(self, reference: str) -> int:
        """Enter a reference and click filter. Returns the result count."""
        ref_input = self._find_reference_input()
        ref_input.fill(reference)

        for selector in ["#question-topic", "#question-subject", "#questionbank-type", "#question-school"]:
            self._clear_if_present(selector)

        self._click_filter()
        return self._read_count()

    def find_edit_link(self, question: dict) -> tuple[str, str]:
        """
        Find the edit link for a question using multi-strategy matching.

        Tries: id+reference+snippet → id → reference+snippet → reference → snippet → single-row fallback.

        Returns (href, match_strategy).
        """
        rows = self._collect_result_rows()
        snippet_token = canonical(snippet(question["question_text"]))
        expected_id = question["id"]

        id_matches, ref_snippet_matches, ref_matches, snippet_matches = [], [], [], []
        all_links: list[tuple[str, str]] = []

        for row in rows:
            href = row["hrefs"][0]
            all_links.append((href, row["text"]))
            href_ids = {self._extract_id(h) for h in row["hrefs"]} - {None}

            if expected_id in href_ids:
                id_matches.append(href)
                if question["reference"] in row["text"] and snippet_token in row["canonical"]:
                    return href, "id+reference+snippet"

            if question["reference"] in row["text"]:
                ref_matches.append(href)
                if snippet_token and snippet_token in row["canonical"]:
                    ref_snippet_matches.append(href)

            if snippet_token and snippet_token in row["canonical"]:
                snippet_matches.append(href)

        for matches, strategy in [
            (id_matches, "id"),
            (ref_snippet_matches, "reference+snippet"),
            (ref_matches, "reference"),
            (snippet_matches, "snippet"),
        ]:
            if len(matches) == 1:
                return matches[0], strategy

        if len(all_links) == 1:
            return all_links[0][0], "single-row-fallback"

        raise AssertionError(
            f"Could not find unique edit link for reference {question['reference']!r}. "
            f"id_matches={len(id_matches)}, ref_matches={len(ref_matches)}"
        )

    def verify_question_type(self, expected_types: set[str]) -> str:
        """Read the question type from the edit page and assert it matches."""
        type_locator = self.page.locator(self.QUESTION_TYPE)
        type_locator.wait_for(state="attached", timeout=10_000)
        actual = normalize(type_locator.input_value())
        assert actual in expected_types, (
            f"Question type mismatch: expected {sorted(expected_types)!r}, got {actual!r}"
        )
        return actual

    def count_resource_images(self) -> int:
        return self.page.locator(self.RESOURCE_IMAGE).count()

    # -- Private helpers --

    def _find_reference_input(self):
        for selector in self.REFERENCE_INPUT_SELECTORS:
            locator = self.page.locator(selector).first
            try:
                locator.wait_for(state="visible", timeout=10_000)
                return locator
            except Exception:
                continue
        raise AssertionError("Could not find the reference filter input")

    def _clear_if_present(self, selector: str) -> None:
        locator = self.page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=2_000)
            tag = locator.evaluate("(el) => el.tagName.toLowerCase()")
            if tag == "select":
                locator.select_option(value="")
            else:
                locator.fill("")
        except Exception:
            pass

    def _click_filter(self) -> None:
        self.page.locator(self.FILTER_BUTTON).first.click()
        self.page.locator(self.RESULT_COUNT).first.wait_for(state="visible", timeout=30_000)

    def _read_count(self) -> int:
        text = normalize(
            self.page.locator(self.RESULT_COUNT).first.text_content()
        ).replace(",", "")
        assert text, "Could not read the filtered question count"
        return int(text)

    def _collect_result_rows(self) -> list[dict]:
        rows = self.page.locator(self.RESULT_ROW)
        collected = []
        for i in range(rows.count()):
            row = rows.nth(i)
            text = normalize(row.inner_text(timeout=5_000))
            links = row.locator(self.EDIT_LINK)
            hrefs = [links.nth(j).get_attribute("href") or "" for j in range(links.count()) if links.nth(j).get_attribute("href")]
            if hrefs:
                collected.append({"text": text, "canonical": canonical(text), "hrefs": hrefs})
        return collected

    @staticmethod
    def _extract_id(href: str) -> str | None:
        match = re.search(r"/admin/questions/edit/(\d+)", href or "")
        return match.group(1) if match else None
