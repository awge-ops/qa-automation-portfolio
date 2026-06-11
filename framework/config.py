"""
Centralized configuration loaded from environment and config/main.env.

All paths, URLs, and credentials are resolved once at import time.
Tests and page objects access values via this module.
"""

import os
from pathlib import Path
from urllib.parse import urlparse


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_PATH = _PROJECT_ROOT / "config" / "main.env"


def _load_env(env_path: Path) -> None:
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


_load_env(_ENV_PATH)


def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


# Chrome remote debugging
DEBUG_HOST: str = os.environ.get("DEBUG_HOST", "127.0.0.1")
DEBUG_PORT: int = int(os.environ.get("DEBUG_PORT", "9333"))
ADMIN_DEBUG_PORT: int = int(os.environ.get("ADMIN_DEBUG_PORT", "9334"))

# Application
APP_ADDRESS: str = os.environ.get("APP_ADDRESS", "http://127.0.0.1:8888").rstrip("/")
APP_PATH: str = os.environ.get("APP_PATH", r"C:\Program Files (x86)\AppUnderTest")
INSTALLER_PATH: str = os.environ.get("INSTALLER_PATH", r".\installers\app-latest.exe")

# Paths
EXPORT_PATH: str = os.environ.get("EXPORT_PATH", r"C:\Automation\test_exports")
DEFAULT_DB_PATH: str = os.environ.get("DEFAULT_DB_PATH", "")
QUESTIONS_DB_PATH: str = os.environ.get("QUESTIONS_DB_PATH", "")
LOG_PATH: str = os.environ.get("LOG_PATH", "")
TMP_PATH: str = os.environ.get("TMP_PATH", "")

# Admin portal
ADMIN_URL: str = os.environ.get("ADMIN_URL", "https://admin.example.com/")
ADMIN_QUESTIONS_URL: str = os.environ.get("ADMIN_QUESTIONS_URL", "https://admin.example.com/admin/questions")
ADMIN_USERNAME: str = os.environ.get("ADMIN_USERNAME", "")
ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "")
ADMIN_LOGIN_TIMEOUT_MS: int = int(os.environ.get("ADMIN_LOGIN_TIMEOUT_MS", "300000"))

# Feature flags
HEADLESS: bool = _env_bool("HEADLESS")
FORCE_SKIP_OVERRIDE: bool = _env_bool("FORCE_SKIP_OVERRIDE")

# Config file paths
CONFIG_DIR = _PROJECT_ROOT / "config"
STUDENTS_INI = CONFIG_DIR / "students.ini"
LESSONS_INI = CONFIG_DIR / "lessons.ini"
QUESTIONS_INI = CONFIG_DIR / "questions.ini"
TESTS_INI = CONFIG_DIR / "tests.ini"
SCHOOLS_INI = CONFIG_DIR / "schools.ini"


def is_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() in {"1", "true", "yes"}
