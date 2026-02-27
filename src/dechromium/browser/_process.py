from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import urlopen

from dechromium._exceptions import BrowserError, BrowserTimeoutError


@dataclass(slots=True)
class BrowserInfo:
    profile_id: str
    pid: int
    debug_port: int
    ws_endpoint: str
    cdp_url: str


class BrowserProcess:
    __slots__ = ("_info", "_proc", "args", "debug_port", "env", "profile_id")

    def __init__(
        self,
        profile_id: str,
        args: list[str],
        env: dict[str, str],
        debug_port: int,
    ):
        self.profile_id = profile_id
        self.args = args
        self.env = env
        self.debug_port = debug_port
        self._proc: subprocess.Popen | None = None
        self._info: BrowserInfo | None = None

    def start(self, timeout: float = 15.0) -> BrowserInfo:
        full_args = [
            *self.args,
            f"--remote-debugging-port={self.debug_port}",
            "--remote-allow-origins=*",
            "--no-sandbox",
        ]

        self._proc = subprocess.Popen(
            full_args,
            env={**os.environ, **self.env},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        cdp_url = f"http://127.0.0.1:{self.debug_port}"

        try:
            ws = self._wait_cdp(cdp_url, timeout)
        except (BrowserTimeoutError, BrowserError):
            self.stop()
            raise

        self._info = BrowserInfo(
            profile_id=self.profile_id,
            pid=self._proc.pid,
            debug_port=self.debug_port,
            ws_endpoint=ws,
            cdp_url=cdp_url,
        )
        return self._info

    def stop(self, timeout: float = 5.0):
        if not self._proc:
            return
        if self._proc.poll() is not None:
            self._proc = None
            self._info = None
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait(timeout=3)
        self._proc = None
        self._info = None

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    @property
    def info(self) -> BrowserInfo | None:
        if self.is_running:
            return self._info
        return None

    def _wait_cdp(self, cdp_url: str, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        last_err: Exception | None = None
        while time.monotonic() < deadline:
            if self._proc and self._proc.poll() is not None:
                raise BrowserError(f"Browser exited with code {self._proc.returncode}")
            try:
                resp = urlopen(f"{cdp_url}/json/version", timeout=2)
                data = json.loads(resp.read())
                return data.get("webSocketDebuggerUrl", "")
            except (URLError, OSError, json.JSONDecodeError) as exc:
                last_err = exc
                time.sleep(0.3)
        raise BrowserTimeoutError(
            f"CDP not ready after {timeout}s on port {self.debug_port}: {last_err}"
        )
