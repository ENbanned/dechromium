from __future__ import annotations

import shutil
import time
from pathlib import Path
from urllib.parse import urlparse

from .config import Config
from .models import (
    Fonts,
    Hardware,
    Identity,
    Network,
    Noise,
    Profile,
    WebGL,
)


_SECTION_MODELS = {
    "identity": Identity,
    "hardware": Hardware,
    "webgl": WebGL,
    "noise": Noise,
    "network": Network,
    "fonts": Fonts,
}

_FONT_GENERICS = {
    "windows": {"sans_serif": "Arial", "serif": "Times New Roman", "monospace": "Courier New"},
    "linux": {"sans_serif": "DejaVu Sans", "serif": "DejaVu Serif", "monospace": "DejaVu Sans Mono"},
    "macos": {"sans_serif": "Helvetica Neue", "serif": "Times New Roman", "monospace": "Courier New"},
}

_LINUX_FONT_BLOCKS = (
    "Liberation Sans", "Liberation Serif", "Liberation Mono",
    "DejaVu Sans", "DejaVu Serif", "DejaVu Sans Mono",
    "Ubuntu", "Noto Sans",
)

_MACOS_FONT_BLOCKS = (
    "Liberation Sans", "Liberation Serif", "Liberation Mono",
    "DejaVu Sans", "DejaVu Serif", "DejaVu Sans Mono",
    "Ubuntu",
)

_ALIAS_BLOCKS: dict[str, tuple[str, ...]] = {
    "windows": _LINUX_FONT_BLOCKS,
    "macos": _MACOS_FONT_BLOCKS,
    "linux": (),
}

_FONTCONFIG_HEADER = """\
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>{font_dir}</dir>
  <cachedir>{cache_dir}</cachedir>

  <alias>
    <family>sans-serif</family>
    <prefer><family>{sans_serif}</family></prefer>
  </alias>
  <alias>
    <family>serif</family>
    <prefer><family>{serif}</family></prefer>
  </alias>
  <alias>
    <family>monospace</family>
    <prefer><family>{monospace}</family></prefer>
  </alias>

  <selectfont>
    <rejectfont>
      <glob>/usr/share/fonts/*</glob>
      <glob>/usr/local/share/fonts/*</glob>
      <glob>~/.fonts/*</glob>
      <glob>~/.local/share/fonts/*</glob>
    </rejectfont>
  </selectfont>
"""

_FONTCONFIG_BLOCK = """\

  <match target="pattern">
    <test name="family"><string>{family}</string></test>
    <edit name="family" mode="assign" binding="same"><string>__BLOCKED__</string></edit>
  </match>"""

_FONTCONFIG_FOOTER = "\n</fontconfig>\n"


class ProfileManager:
    def __init__(self, config: Config):
        self.config = config
        self.config.profiles_dir.mkdir(parents=True, exist_ok=True)

    def create(self, name: str = "default", **overrides) -> Profile:
        profile = Profile(name=name)
        self._apply_overrides(profile, overrides)

        pdir = self._profile_dir(profile.id)
        pdir.mkdir(parents=True, exist_ok=True)
        self._data_dir(profile.id).mkdir(exist_ok=True)
        self._generate_fonts_conf(profile)
        self._save(profile)
        return profile

    def get(self, profile_id: str) -> Profile:
        path = self._config_path(profile_id)
        if not path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_id}")
        return Profile.model_validate_json(path.read_text())

    def list_all(self) -> list[Profile]:
        result = []
        if not self.config.profiles_dir.exists():
            return result
        for pdir in sorted(self.config.profiles_dir.iterdir()):
            cfg = pdir / "profile.json"
            if cfg.exists():
                result.append(Profile.model_validate_json(cfg.read_text()))
        return result

    def update(self, profile_id: str, **overrides) -> Profile:
        profile = self.get(profile_id)
        profile.updated_at = int(time.time())
        self._apply_overrides(profile, overrides)
        self._generate_fonts_conf(profile)
        self._save(profile)
        return profile

    def delete(self, profile_id: str) -> bool:
        pdir = self._profile_dir(profile_id)
        if not pdir.exists():
            return False
        shutil.rmtree(pdir)
        return True

    def launch_args(self, profile_id: str) -> list[str]:
        profile = self.get(profile_id)
        net = profile.network
        hw = profile.hardware
        ident = profile.identity
        langs = ",".join(net.languages)

        args = [
            str(self.config.browser_bin),
            f"--user-data-dir={self._data_dir(profile_id)}",
            f"--user-agent={ident.user_agent}",
            f"--lang={net.locale}",
            f"--accept-lang={langs}",
            f"--window-size={hw.screen_width},{hw.screen_height}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled",
        ]

        if net.proxy:
            args.append(f"--proxy-server={net.proxy}")
            proxy_host = urlparse(net.proxy).hostname or ""
            resolver_rules = f"MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE {proxy_host}"
            args.append(f"--host-resolver-rules={resolver_rules}")
            args.append(f"--force-webrtc-ip-handling-policy={net.webrtc_policy}")
            if net.proxy_username:
                args.append(f"--aspect-proxy-username={net.proxy_username}")
            if net.proxy_password:
                args.append(f"--aspect-proxy-password={net.proxy_password}")

        canvas_seed = int(profile.noise.canvas_seed, 16)
        audio_seed = int(profile.noise.audio_seed, 16)

        args.extend([
            f"--aspect-platform={ident.platform}",
            f"--aspect-hardware-concurrency={hw.cores}",
            f"--aspect-device-memory={hw.memory_gb}",
            f"--aspect-screen-width={hw.screen_width}",
            f"--aspect-screen-height={hw.screen_height}",
            f"--aspect-screen-avail-width={hw.avail_width}",
            f"--aspect-screen-avail-height={hw.avail_height}",
            f"--aspect-color-depth={hw.color_depth}",
            f"--aspect-device-pixel-ratio={hw.device_pixel_ratio}",
            f"--aspect-ua-platform={ident.ua_platform}",
            f"--aspect-ua-platform-version={ident.ua_platform_version}",
            f"--aspect-ua-arch={ident.ua_arch}",
            f"--aspect-canvas-noise-seed={canvas_seed}",
            f"--aspect-audio-noise-seed={audio_seed}",
            f"--aspect-webgl-vendor={profile.webgl.vendor}",
            f"--aspect-webgl-renderer={profile.webgl.renderer}",
        ])

        return args

    def launch_env(self, profile_id: str) -> dict[str, str]:
        profile = self.get(profile_id)
        conf = self._fonts_conf_path(profile_id)
        if not conf.exists():
            self._generate_fonts_conf(profile)
        posix_locale = profile.network.locale.replace("-", "_") + ".UTF-8"
        return {
            "FONTCONFIG_FILE": str(conf),
            "TZ": profile.network.timezone,
            "LANG": posix_locale,
        }

    def data_dir(self, profile_id: str) -> Path:
        return self._data_dir(profile_id)

    def _profile_dir(self, profile_id: str) -> Path:
        return self.config.profiles_dir / profile_id

    def _config_path(self, profile_id: str) -> Path:
        return self._profile_dir(profile_id) / "profile.json"

    def _data_dir(self, profile_id: str) -> Path:
        return self._profile_dir(profile_id) / "chrome_data"

    def _fonts_dir(self, profile_id: str) -> Path:
        return self._profile_dir(profile_id) / "fonts"

    def _fonts_conf_path(self, profile_id: str) -> Path:
        return self._profile_dir(profile_id) / "fonts.conf"

    def _fonts_cache_dir(self, profile_id: str) -> Path:
        return self._profile_dir(profile_id) / "fonts_cache"

    def _save(self, profile: Profile):
        self._config_path(profile.id).write_text(profile.model_dump_json(indent=2))

    def _apply_overrides(self, profile: Profile, overrides: dict):
        for section_name, model_cls in _SECTION_MODELS.items():
            if section_name not in overrides:
                continue
            current = getattr(profile, section_name).model_dump()
            updates = overrides[section_name]
            if not isinstance(updates, dict):
                continue
            current.update(updates)
            if section_name == "identity" and "user_agent" not in updates:
                current["user_agent"] = ""
            setattr(profile, section_name, model_cls(**current))

        for field in ("name", "notes"):
            if field in overrides:
                setattr(profile, field, overrides[field])

    def _generate_fonts_conf(self, profile: Profile):
        pack = profile.fonts.font_pack
        src_dir = self.config.fonts_dir / pack
        dst_dir = self._fonts_dir(profile.id)
        cache_dir = self._fonts_cache_dir(profile.id)

        dst_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)

        if src_dir.exists():
            for ttf in src_dir.glob("*.ttf"):
                dst = dst_dir / ttf.name
                if not dst.exists():
                    shutil.copy2(ttf, dst)

        generics = _FONT_GENERICS.get(pack, _FONT_GENERICS["windows"])
        blocks = _ALIAS_BLOCKS.get(pack, ())

        conf = _FONTCONFIG_HEADER.format(
            font_dir=str(dst_dir),
            cache_dir=str(cache_dir),
            sans_serif=generics["sans_serif"],
            serif=generics["serif"],
            monospace=generics["monospace"],
        )
        for family in blocks:
            conf += _FONTCONFIG_BLOCK.format(family=family)
        conf += _FONTCONFIG_FOOTER

        self._fonts_conf_path(profile.id).write_text(conf)
