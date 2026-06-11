"""
Custom Allure result builder for non-pytest contexts.

Generates Allure-compatible JSON that integrates with the standard Allure report.
Used by orchestrators that need fine-grained step control beyond what allure-pytest provides.
"""

import json
import locale
import os
import platform
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Optional


def now_ms() -> int:
    return int(time.time() * 1000)


def make_result(
    name: str,
    full_name: str,
    test_uuid: str,
    start_ms: int,
    suite_name: str = "Test Suite",
    log_names: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Create an Allure result skeleton with optional log attachments."""
    attachments = []
    for key, label, mime in [
        ("laravel_log", "Laravel Log", "text/plain"),
        ("network_log", "Network Log", "text/plain"),
        ("network_har", "Network HAR", "application/json"),
        ("network_summary", "Network Summary", "application/json"),
    ]:
        if log_names and key in log_names:
            attachments.append({"name": label, "type": mime, "source": log_names[key]})

    return {
        "uuid": test_uuid,
        "name": name,
        "fullName": full_name,
        "status": None,
        "statusDetails": {},
        "start": start_ms,
        "stop": None,
        "stage": "finished",
        "steps": [],
        "attachments": attachments,
        "labels": [{"name": "suite", "value": suite_name}],
    }


def add_step(result: dict[str, Any], name: str, fn: Callable) -> None:
    """Execute a callable as a named Allure step, recording pass/fail."""
    step = {
        "name": name,
        "status": None,
        "stage": "finished",
        "steps": [],
        "attachments": [],
        "start": now_ms(),
        "stop": None,
    }
    try:
        fn()
        step["status"] = "passed"
    except Exception:
        step["status"] = "failed"
        step["statusDetails"] = {
            "message": traceback.format_exception_only(*__import__("sys").exc_info()[:2])[0].strip(),
            "trace": traceback.format_exc(),
        }
        raise
    finally:
        step["stop"] = now_ms()
        result["steps"].append(step)


class OutcomeClassifier:
    """Maps exceptions to Allure statuses (passed/failed/broken)."""

    INFRASTRUCTURE_ERRORS = (ConnectionError, OSError)
    ASSERTION_ERRORS = (AssertionError,)

    @classmethod
    def classify(cls, exc: Optional[Exception]) -> tuple[str, dict]:
        if exc is None:
            return "passed", {}

        trace_info = {"message": str(exc), "trace": traceback.format_exc()}

        if isinstance(exc, cls.INFRASTRUCTURE_ERRORS):
            return "broken", trace_info
        if isinstance(exc, cls.ASSERTION_ERRORS):
            return "failed", trace_info
        return "broken", trace_info


def save_result(result: dict[str, Any], export_dir: str, stem: str, test_uuid: str) -> str:
    """Write an Allure result JSON to disk."""
    os.makedirs(export_dir, exist_ok=True)
    filename = f"{stem}_{test_uuid}-result.json"
    out_path = os.path.join(export_dir, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return out_path


def environment_labels() -> list[dict[str, str]]:
    """Generate environment metadata for Allure results."""
    now = datetime.now().astimezone()
    offset = now.utcoffset()
    total_seconds = int(offset.total_seconds()) if offset else 0
    hours, minutes = divmod(abs(total_seconds), 3600)
    sign = "+" if total_seconds >= 0 else "-"
    tz = f"GMT{sign}{hours:02d}{minutes // 60:02d}"

    return [
        {"name": "Computer", "value": platform.node()},
        {"name": "Operating System", "value": f"{platform.system()} {platform.release()} ({platform.version()})"},
        {"name": "System Language", "value": str(locale.getlocale())},
        {"name": "Timezone", "value": tz},
    ]
