"""
Desktop application installation and upgrade tests.

Covers:
  - Silent installation via installer executable
  - Post-install configuration (service management, .env updates)
  - Application log verification after install
  - Upgrade via updater.exe with GUI automation (pywinauto)
  - Service state management during upgrade

These tests run directly on Windows using subprocess and pywinauto,
not through a browser.
"""

import time
from pathlib import Path

import pytest

from framework import config
from framework.helpers.waiters import wait_for_log_content, wait_for_path, wait_for_process_exit


@pytest.mark.desktop
class TestSilentInstallation:
    """Fresh installation of the desktop application."""

    def test_run_installer(self, windows_client):
        """Silent installer should complete without error."""
        result = windows_client.run(f'"{config.INSTALLER_PATH}" /quiet /norestart')
        assert result.success, f"Installer failed: {result.stderr}"

    def test_install_directory_created(self, windows_client):
        """Installation directory should exist after install."""
        assert wait_for_path(config.APP_PATH, timeout=90), (
            f"Install directory not found: {config.APP_PATH}"
        )

    def test_post_install_files_exist(self):
        """Key application files should be present after installation."""
        required_files = [
            Path(config.APP_PATH) / "ATPdigital.exe",
            Path(config.DEFAULT_DB_PATH),
        ]
        for path in required_files:
            assert path.exists(), f"Required file not found: {path}"


@pytest.mark.desktop
class TestPostInstallConfig:
    """Service configuration after installation."""

    SERVICE_NAME = "ATPdigitalQueue"

    def test_stop_service(self, windows_client):
        """Application service should stop without error."""
        result = windows_client.run(f'sc stop "{self.SERVICE_NAME}"')
        time.sleep(5)
        status = windows_client.run(f'sc query "{self.SERVICE_NAME}"')
        assert "STOPPED" in status.stdout or result.success

    def test_update_env_config(self, windows_client):
        """API host in .env should be updatable via PowerShell."""
        env_path = config.APP_PATH + r"\server\application\.env"
        new_host = "https://api.example.com"

        result = windows_client.run_powershell(
            f"(Get-Content -Path '{env_path}') "
            f"-replace 'API_HOST=.*', 'API_HOST={new_host}' "
            f"| Set-Content -Path '{env_path}'"
        )
        assert result.success, f"Failed to update .env: {result.stderr}"

    def test_start_service(self, windows_client):
        """Application service should start after configuration."""
        result = windows_client.run(f'sc start "{self.SERVICE_NAME}"')
        assert result.success, f"Failed to start service: {result.stderr}"


@pytest.mark.desktop
class TestApplicationLogVerification:
    """Verify application logs after installation."""

    def test_laravel_log_shows_update_complete(self):
        """Application log should contain update completion messages."""
        assert wait_for_log_content(
            config.LOG_PATH,
            expected_lines=["Processing application update", "Application updates complete"],
            timeout=120,
            interval=5,
        ), "Expected log lines not found within timeout"


@pytest.mark.desktop
@pytest.mark.slow
class TestUpgrade:
    """Application upgrade via the built-in updater."""

    def test_modify_updater_config(self):
        """updater.ini should be modifiable to point to a new update URL."""
        updater_ini = Path(config.APP_PATH) / "updater.ini"
        assert updater_ini.exists(), f"updater.ini not found at {updater_ini}"

        lines = updater_ini.read_text(encoding="utf-8").splitlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith("URL="):
                new_lines.append("URL=https://updates.example.com/latest/update.txt")
            else:
                new_lines.append(line)
        updater_ini.write_text("\n".join(new_lines), encoding="utf-8")

    def test_run_updater(self, windows_client):
        """
        Updater should complete the update flow.

        Note: This test uses pywinauto for native Windows UI automation
        (clicking Next/Install/Finish in the installer wizard).
        """
        try:
            from pywinauto import Application as WinApp
        except ImportError:
            pytest.skip("pywinauto not available")

        updater_exe = str(Path(config.APP_PATH) / "updater.exe")
        app = WinApp(backend="uia").start(f'"{updater_exe}" /checknow')

        time.sleep(2)
        dlg = WinApp(backend="uia").connect(title_re=".*Setup.*").window(title_re=".*Setup.*")
        dlg.Next.click_input()
        time.sleep(3)
        dlg.Install.click_input()

        finish_btn = dlg.child_window(title="Finish", control_type="Button")
        assert finish_btn.exists(timeout=300), "Finish button not found after installation"
        finish_btn.click_input()

    def test_add_automated_testing_flag(self, windows_client):
        """AUTOMATED_TESTING=true should be present in .env after upgrade."""
        env_path = config.APP_PATH + r"\server\application\.env"
        result = windows_client.run_powershell(
            f"$c = Get-Content -Path '{env_path}'; "
            f"if (-not ($c -match 'AUTOMATED_TESTING=')) {{ "
            f"$c += 'AUTOMATED_TESTING=true'; "
            f"Set-Content -Path '{env_path}' -Value $c -Encoding UTF8 }}"
        )
        assert result.success, f"Failed to add AUTOMATED_TESTING flag: {result.stderr}"
