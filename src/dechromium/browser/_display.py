from __future__ import annotations

import shutil
import subprocess
import time

from dechromium._exceptions import DisplayError


class VirtualDisplay:
    __slots__ = ("_proc", "display", "resolution")

    def __init__(self, display: int = 99, resolution: str = "1920x1080x24"):
        self.display = display
        self.resolution = resolution
        self._proc: subprocess.Popen | None = None

    @property
    def display_str(self) -> str:
        return f":{self.display}"

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self):
        if self.is_running:
            return

        if not shutil.which("Xvfb"):
            raise DisplayError("Xvfb not found. Install with: apt install xvfb")

        self._proc = subprocess.Popen(
            [
                "Xvfb",
                self.display_str,
                "-screen",
                "0",
                self.resolution,
                "-ac",
                "-nolisten",
                "tcp",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(0.5)
        if self._proc.poll() is not None:
            code = self._proc.returncode
            self._proc = None
            raise DisplayError(f"Xvfb exited immediately with code {code}")

    def stop(self):
        if not self._proc:
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait(timeout=2)
        self._proc = None
