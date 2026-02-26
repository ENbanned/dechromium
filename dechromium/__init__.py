from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from .browser import BrowserInfo, BrowserPool
from .config import Config
from .cookies import export_cookies, import_cookies
from .manager import ProfileManager
from .models import (
    PLATFORMS,
    Fonts,
    Hardware,
    Identity,
    Network,
    Noise,
    Profile,
    WebGL,
)

__version__ = "0.1.0"


class Dechromium:
    def __init__(self, config: Config | None = None, **kwargs):
        self.config = config or Config(**kwargs)
        self._manager = ProfileManager(self.config)
        self._pool = BrowserPool(
            port_start=self.config.debug_port_start,
            port_end=self.config.debug_port_end,
        )

    def create(
        self,
        name: str = "default",
        *,
        platform: str | None = None,
        proxy: str | None = None,
        timezone: str | None = None,
        locale: str | None = None,
        languages: list[str] | None = None,
        cores: int | None = None,
        memory_gb: float | None = None,
        screen: tuple[int, int] | None = None,
        webgl_vendor: str | None = None,
        webgl_renderer: str | None = None,
        identity: dict | None = None,
        hardware: dict | None = None,
        webgl: dict | None = None,
        noise: dict | None = None,
        network: dict | None = None,
        fonts: dict | None = None,
        notes: str = "",
    ) -> Profile:
        overrides = _build_overrides(
            platform=platform,
            proxy=proxy,
            timezone=timezone,
            locale=locale,
            languages=languages,
            cores=cores,
            memory_gb=memory_gb,
            screen=screen,
            webgl_vendor=webgl_vendor,
            webgl_renderer=webgl_renderer,
            identity=identity,
            hardware=hardware,
            webgl=webgl,
            noise=noise,
            network=network,
            fonts=fonts,
            notes=notes,
        )
        return self._manager.create(name, **overrides)

    def get(self, profile_id: str) -> Profile:
        return self._manager.get(profile_id)

    def list(self) -> list[Profile]:
        return self._manager.list_all()

    def update(
        self,
        profile_id: str,
        *,
        name: str | None = None,
        notes: str | None = None,
        identity: dict | None = None,
        hardware: dict | None = None,
        webgl: dict | None = None,
        noise: dict | None = None,
        network: dict | None = None,
        fonts: dict | None = None,
    ) -> Profile:
        overrides: dict = {}
        if name is not None:
            overrides["name"] = name
        if notes is not None:
            overrides["notes"] = notes
        for key, val in [
            ("identity", identity),
            ("hardware", hardware),
            ("webgl", webgl),
            ("noise", noise),
            ("network", network),
            ("fonts", fonts),
        ]:
            if val is not None:
                overrides[key] = val
        return self._manager.update(profile_id, **overrides)

    def delete(self, profile_id: str) -> bool:
        try:
            self._pool.stop(profile_id)
        except Exception:
            pass
        return self._manager.delete(profile_id)

    def start(
        self,
        profile_id: str,
        headless: bool = True,
        extra_args: list[str] | None = None,
        timeout: float = 15.0,
    ) -> BrowserInfo:
        args = self._manager.launch_args(profile_id)
        env = self._manager.launch_env(profile_id)
        return self._pool.start(
            profile_id,
            args,
            env,
            headless=headless,
            extra_args=extra_args,
            timeout=timeout,
        )

    def stop(self, profile_id: str) -> bool:
        return self._pool.stop(profile_id)

    def stop_all(self):
        self._pool.stop_all()

    def status(self, profile_id: str) -> dict:
        return self._pool.status(profile_id)

    def running(self) -> list[BrowserInfo]:
        return self._pool.list_running()

    def import_cookies(self, profile_id: str, source: str | list[dict]) -> int:
        data_dir = self._manager.data_dir(profile_id)
        if isinstance(source, str):
            return import_cookies(data_dir, Path(source))
        return import_cookies(data_dir, source)

    def export_cookies(self, profile_id: str) -> list[dict]:
        data_dir = self._manager.data_dir(profile_id)
        return export_cookies(data_dir)

    def serve(self, host: str | None = None, port: int | None = None):
        try:
            from .server import create_app
        except ImportError:
            raise ImportError(
                "Server dependencies not installed. "
                "Install with: pip install dechromium[server]"
            )
        import uvicorn

        app = create_app(self)
        uvicorn.run(
            app,
            host=host or self.config.api_host,
            port=port or self.config.api_port,
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop_all()

    def __repr__(self) -> str:
        n_profiles = len(self._manager.list_all())
        n_running = len(self._pool.list_running())
        return f"Dechromium(profiles={n_profiles}, running={n_running})"


def _build_overrides(
    platform: str | None = None,
    proxy: str | None = None,
    timezone: str | None = None,
    locale: str | None = None,
    languages: list[str] | None = None,
    cores: int | None = None,
    memory_gb: float | None = None,
    screen: tuple[int, int] | None = None,
    webgl_vendor: str | None = None,
    webgl_renderer: str | None = None,
    identity: dict | None = None,
    hardware: dict | None = None,
    webgl: dict | None = None,
    noise: dict | None = None,
    network: dict | None = None,
    fonts: dict | None = None,
    notes: str = "",
) -> dict:
    result: dict = {}

    if platform and platform in PLATFORMS:
        preset = PLATFORMS[platform]
        result["identity"] = dict(preset["identity"])
        result["webgl"] = dict(preset["webgl"])
        result["fonts"] = dict(preset["fonts"])

    if identity:
        result.setdefault("identity", {}).update(identity)
    if hardware:
        result.setdefault("hardware", {}).update(hardware)
    if webgl:
        result.setdefault("webgl", {}).update(webgl)
    if noise:
        result["noise"] = noise
    if network:
        result.setdefault("network", {}).update(network)
    if fonts:
        result.setdefault("fonts", {}).update(fonts)

    if proxy:
        parsed = urlparse(proxy)
        net = result.setdefault("network", {})
        if parsed.username:
            clean_proxy = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
            net["proxy"] = clean_proxy
            net["proxy_username"] = parsed.username
            net.setdefault("proxy_password", parsed.password or "")
        else:
            net["proxy"] = proxy

    if timezone:
        result.setdefault("network", {})["timezone"] = timezone
    if locale:
        result.setdefault("network", {})["locale"] = locale
    if languages:
        result.setdefault("network", {})["languages"] = languages

    if cores is not None:
        result.setdefault("hardware", {})["cores"] = cores
    if memory_gb is not None:
        result.setdefault("hardware", {})["memory_gb"] = memory_gb
    if screen:
        hw = result.setdefault("hardware", {})
        hw["screen_width"] = screen[0]
        hw["screen_height"] = screen[1]
        hw["avail_width"] = screen[0]
        hw["avail_height"] = screen[1] - 40

    if webgl_vendor:
        result.setdefault("webgl", {})["vendor"] = webgl_vendor
    if webgl_renderer:
        result.setdefault("webgl", {})["renderer"] = webgl_renderer

    if notes:
        result["notes"] = notes

    return result


__all__ = [
    "Dechromium",
    "Config",
    "Profile",
    "Identity",
    "Hardware",
    "WebGL",
    "Noise",
    "Network",
    "Fonts",
    "BrowserInfo",
    "PLATFORMS",
]
