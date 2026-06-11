"""
SQLite database schema and integrity tests.

Verifies:
  - Required tables exist with correct columns
  - NOT NULL constraints are enforced
  - Referential integrity between related tables
  - Valid enumeration values (e.g. syllabus versions)
  - Non-empty data in critical tables
"""

import pytest


def _table_exists(conn, table_name: str) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _column_names(conn, table_name: str) -> list[str]:
    cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
    return [row[1] for row in cursor.fetchall()]


def _row_count(conn, table_name: str) -> int:
    cursor = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]")
    return cursor.fetchone()[0]


def _null_count(conn, table_name: str, column: str) -> int:
    cursor = conn.execute(f"SELECT COUNT(*) FROM [{table_name}] WHERE [{column}] IS NULL")
    return cursor.fetchone()[0]


@pytest.mark.database
class TestSyllabusSchema:
    """Syllabus table structure and integrity."""

    REQUIRED_TABLES = ["syllabus", "syllabus_module", "syllabus_question_bank", "syllabus_subject"]

    SYLLABUS_COLUMNS = ["id", "name", "version", "licence"]
    SYLLABUS_NOT_NULL = ["id", "name", "version"]
    VALID_VERSIONS = {"2016", "2018", "2020"}

    @pytest.mark.parametrize("table", REQUIRED_TABLES)
    def test_table_exists(self, default_db, table):
        assert _table_exists(default_db, table), f"Table '{table}' does not exist"

    @pytest.mark.parametrize("column", SYLLABUS_COLUMNS)
    def test_syllabus_has_column(self, default_db, column):
        columns = _column_names(default_db, "syllabus")
        assert column in columns, f"Column '{column}' missing from syllabus table. Found: {columns}"

    @pytest.mark.parametrize("column", SYLLABUS_NOT_NULL)
    def test_syllabus_no_null_values(self, default_db, column):
        nulls = _null_count(default_db, "syllabus", column)
        assert nulls == 0, f"Found {nulls} NULL values in syllabus.{column}"

    def test_syllabus_versions_valid(self, default_db):
        """All syllabus version values must be in the allowed set."""
        cursor = default_db.execute("SELECT DISTINCT version FROM syllabus")
        versions = {str(row[0]) for row in cursor.fetchall()}
        invalid = versions - self.VALID_VERSIONS
        assert not invalid, f"Invalid syllabus versions: {invalid}. Allowed: {self.VALID_VERSIONS}"

    def test_syllabus_referential_integrity(self, default_db):
        """Every syllabus.id must appear in each related table."""
        cursor = default_db.execute("SELECT id FROM syllabus")
        syllabus_ids = {row[0] for row in cursor.fetchall()}

        for related_table in ["syllabus_module", "syllabus_question_bank", "syllabus_subject"]:
            if not _table_exists(default_db, related_table):
                continue
            cursor = default_db.execute(f"SELECT DISTINCT syllabus_id FROM [{related_table}]")
            related_ids = {row[0] for row in cursor.fetchall()}
            missing = syllabus_ids - related_ids
            assert not missing, (
                f"Syllabus IDs {missing} have no entries in {related_table}"
            )

    def test_syllabus_has_records(self, default_db):
        count = _row_count(default_db, "syllabus")
        assert count > 0, "syllabus table is empty"


@pytest.mark.database
class TestModuleSchema:
    """Module table structure and integrity."""

    REQUIRED_TABLES = ["module", "syllabus_module", "module_structure"]
    MODULE_COLUMNS = ["id", "name", "description"]

    @pytest.mark.parametrize("table", REQUIRED_TABLES)
    def test_table_exists(self, default_db, table):
        assert _table_exists(default_db, table), f"Table '{table}' does not exist"

    @pytest.mark.parametrize("column", MODULE_COLUMNS)
    def test_module_has_column(self, default_db, column):
        columns = _column_names(default_db, "module")
        assert column in columns, f"Column '{column}' missing from module table. Found: {columns}"

    def test_module_referential_integrity(self, default_db):
        """Every module.id must appear in syllabus_module and module_structure."""
        cursor = default_db.execute("SELECT id FROM module")
        module_ids = {row[0] for row in cursor.fetchall()}

        for related_table in ["syllabus_module", "module_structure"]:
            if not _table_exists(default_db, related_table):
                continue
            cursor = default_db.execute(f"SELECT DISTINCT module_id FROM [{related_table}]")
            related_ids = {row[0] for row in cursor.fetchall()}
            missing = module_ids - related_ids
            assert not missing, (
                f"Module IDs {missing} have no entries in {related_table}"
            )

    def test_module_has_records(self, default_db):
        count = _row_count(default_db, "module")
        assert count > 0, "module table is empty"
