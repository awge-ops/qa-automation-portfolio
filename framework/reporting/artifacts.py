"""
Failure artifact collector.

On test failure, collects diagnostic artifacts from the system under test:
  - Application logs
  - SQLite databases
  - Temp folder archive
  - Windows Event Viewer export
  - HAR network recordings
"""

import os
import shutil
import subprocess
from typing import Optional

from framework import config


def _copy_artifact(source: Optional[str], destination: str) -> Optional[str]:
    if not source or not os.path.exists(source):
        return None
    try:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(source, destination)
        return destination
    except Exception:
        return None


def collect_failure_artifacts(export_dir: str, test_uuid: str) -> list[dict[str, str]]:
    """
    Collect runtime artifacts for a failed/broken test.

    Returns attachment metadata for each successfully collected artifact.
    """
    os.makedirs(export_dir, exist_ok=True)
    collected: list[dict[str, str]] = []

    artifact_map = [
        (config.LOG_PATH, f"{test_uuid}-laravel.log", "Application Log", "text/plain"),
        (config.DEFAULT_DB_PATH, f"{test_uuid}-default.db", "Default DB", "application/octet-stream"),
        (config.QUESTIONS_DB_PATH, f"{test_uuid}-questions.db", "Questions DB", "application/octet-stream"),
    ]

    for source, filename, label, mime in artifact_map:
        dest = os.path.join(export_dir, filename)
        if _copy_artifact(source, dest):
            collected.append({"name": label, "type": mime, "source": filename})

    if config.TMP_PATH and os.path.isdir(config.TMP_PATH):
        try:
            archive_base = os.path.join(export_dir, f"{test_uuid}-tmp")
            shutil.make_archive(archive_base, "zip", config.TMP_PATH)
            collected.append({"name": "Tmp Folder", "type": "application/zip", "source": f"{test_uuid}-tmp.zip"})
        except Exception:
            pass

    try:
        evtx_path = os.path.join(export_dir, f"{test_uuid}-eventviewer.evtx")
        subprocess.run(
            ["wevtutil", "epl", "Application", evtx_path],
            check=True, capture_output=True,
        )
        collected.append({"name": "Event Viewer", "type": "application/octet-stream", "source": f"{test_uuid}-eventviewer.evtx"})
    except Exception:
        pass

    return collected
