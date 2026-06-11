"""Polling utilities for waiting on external state changes."""

import os
import time
from typing import Optional

import psutil


def wait_for_log_content(
    log_path: str,
    expected_lines: list[str],
    timeout: int = 120,
    interval: int = 5,
) -> bool:
    """Poll a log file until all expected lines are present."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with open(log_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
            if all(line in content for line in expected_lines):
                return True
        except OSError:
            pass
        time.sleep(interval)
    return False


def wait_for_process_exit(
    process_name: str,
    timeout: int = 300,
    interval: int = 2,
) -> bool:
    """Wait until a named process is no longer running."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(
            p.info["name"].lower() == process_name.lower()
            for p in psutil.process_iter(["name"])
        ):
            return True
        time.sleep(interval)
    return False


def wait_for_path(
    path: str,
    timeout: int = 90,
    interval: int = 2,
) -> bool:
    """Wait until a filesystem path exists."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(path):
            return True
        time.sleep(interval)
    return False
