"""
Windows subprocess execution client.

Provides a uniform interface for running shell commands on the local Windows machine
with real-time output streaming and structured result handling.
"""

import logging
import platform
import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class WindowsClient:
    """Execute commands on the local Windows machine via subprocess."""

    def __init__(self, logger: logging.Logger | None = None):
        if platform.system() != "Windows":
            raise RuntimeError("WindowsClient can only be used on Windows")
        self.logger = logger or logging.getLogger(__name__)

    def run(self, command: str, timeout: int | None = None) -> CommandResult:
        """
        Execute a command and stream output in real-time.

        Returns a CommandResult with exit_code, stdout, and stderr.
        """
        self.logger.info("[EXEC] %s", command)

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            lines: list[str] = []
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                line = output.rstrip("\n\r")
                if line:
                    lines.append(line)
                    self.logger.info("[OUT] %s", line)

            exit_code = process.returncode or 0
            self.logger.info("[DONE] exit_code=%d", exit_code)

            return CommandResult(
                exit_code=exit_code,
                stdout="\n".join(lines),
                stderr="",
            )

        except subprocess.TimeoutExpired:
            self.logger.error("[TIMEOUT] Command timed out")
            return CommandResult(exit_code=1, stdout="", stderr="Command timed out")
        except Exception as exc:
            self.logger.error("[ERROR] %s", exc)
            return CommandResult(exit_code=1, stdout="", stderr=str(exc))

    def run_powershell(self, script: str, timeout: int | None = None) -> CommandResult:
        """Execute a PowerShell script via powershell.exe."""
        return self.run(f'powershell -NoProfile -Command "{script}"', timeout=timeout)
