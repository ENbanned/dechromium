from __future__ import annotations

import os
import socket
import sys

from dechromium._exceptions import BrowserError

from ._process import BrowserInfo, BrowserProcess

if sys.platform != "win32":
    from ._display import VirtualDisplay


class BrowserPool:
    def __init__(self, port_start: int = 9200, port_end: int = 9999):
        self._browsers: dict[str, BrowserProcess] = {}
        self._port_start = port_start
        self._port_end = port_end
        self._next_port = port_start
        self._display: VirtualDisplay | None = None

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
        launch_env = dict(env)
        if headless:
            launch_args.append("--headless=new")
        elif sys.platform != "win32":
            if not self._display:
                self._display = VirtualDisplay()
            if not self._display.is_running:
                self._display.start()
            launch_env["DISPLAY"] = self._display.display_str
        if sys.platform == "win32":
            if headless:
                launch_args.append("--enable-unsafe-swiftshader")
        elif not os.environ.get("DISPLAY") or not headless:
            launch_args.append("--enable-unsafe-swiftshader")
        if extra_args:
            launch_args.extend(extra_args)

        port = self._allocate_port()
        proc = BrowserProcess(profile_id, launch_args, launch_env, port)
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
        if self._display:
            self._display.stop()
            self._display = None

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
        raise BrowserError(f"No free ports in range {self._port_start}-{self._port_end}")

    @staticmethod
    def _is_port_free(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return True
        except OSError:
            return False
