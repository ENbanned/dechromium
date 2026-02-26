from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import urlopen


@dataclass(slots=True)
class BrowserInfo:
    profile_id: str
    pid: int
    debug_port: int
    ws_endpoint: str
    cdp_url: str


class BrowserProcess:
    __slots__ = ("profile_id", "args", "env", "debug_port", "_proc", "_info")

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
        full_args = self.args + [
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
        except (TimeoutError, RuntimeError):
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
                raise RuntimeError(
                    f"Browser exited with code {self._proc.returncode}"
                )
            try:
                resp = urlopen(f"{cdp_url}/json/version", timeout=2)
                data = json.loads(resp.read())
                return data.get("webSocketDebuggerUrl", "")
            except (URLError, OSError, json.JSONDecodeError) as exc:
                last_err = exc
                time.sleep(0.3)
        raise TimeoutError(
            f"CDP not ready after {timeout}s on port {self.debug_port}: {last_err}"
        )


class BrowserPool:
    def __init__(self, port_start: int = 9200, port_end: int = 9999):
        self._browsers: dict[str, BrowserProcess] = {}
        self._port_start = port_start
        self._port_end = port_end
        self._next_port = port_start

    def start(
        self,
        profile_id: str,
        args: list[str],
        env: dict[str, str],
        headless: bool = True,
        extra_args: list[str] | None = None,
        timeout: float = 15.0,
    ) -> BrowserInfo:
        existing = self._browsers.get(profile_id)
        if existing and existing.is_running and existing.info:
            return existing.info

        launch_args = list(args)
        if headless:
            launch_args.extend(["--headless=new", "--enable-unsafe-swiftshader"])
        if extra_args:
            launch_args.extend(extra_args)

        port = self._allocate_port()
        proc = BrowserProcess(profile_id, launch_args, env, port)
        info = proc.start(timeout=timeout)
        self._browsers[profile_id] = proc
        return info

    def stop(self, profile_id: str) -> bool:
        proc = self._browsers.pop(profile_id, None)
        if not proc:
            return False
        proc.stop()
        return True

    def stop_all(self):
        for proc in self._browsers.values():
            proc.stop()
        self._browsers.clear()

    def status(self, profile_id: str) -> dict:
        proc = self._browsers.get(profile_id)
        if proc and proc.is_running and proc.info:
            info = proc.info
            return {
                "status": "running",
                "profile_id": info.profile_id,
                "pid": info.pid,
                "debug_port": info.debug_port,
                "ws_endpoint": info.ws_endpoint,
                "cdp_url": info.cdp_url,
            }
        return {"status": "stopped", "profile_id": profile_id}

    def list_running(self) -> list[BrowserInfo]:
        result = []
        dead = []
        for pid, proc in self._browsers.items():
            if proc.is_running and proc.info:
                result.append(proc.info)
            elif not proc.is_running:
                dead.append(pid)
        for pid in dead:
            self._browsers.pop(pid, None)
        return result

    def _allocate_port(self) -> int:
        total = self._port_end - self._port_start + 1
        for _ in range(total):
            port = self._next_port
            self._next_port += 1
            if self._next_port > self._port_end:
                self._next_port = self._port_start
            if self._is_port_free(port):
                return port
        raise RuntimeError(
            f"No free ports in range {self._port_start}-{self._port_end}"
        )

    @staticmethod
    def _is_port_free(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return True
        except OSError:
            return False
