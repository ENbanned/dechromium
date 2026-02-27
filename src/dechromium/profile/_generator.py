from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).parent.parent / "data"
_DB_CACHE: dict | None = None


def _load_db() -> dict:
    global _DB_CACHE
    if _DB_CACHE is None:
        with open(_DATA_DIR / "gpu_profiles.json") as f:
            _DB_CACHE = json.load(f)
    return _DB_CACHE


def _weighted_choice(items: list[dict], rng: random.Random) -> dict:
    weights = [it["weight"] for it in items]
    return rng.choices(items, weights=weights, k=1)[0]


def _weighted_screen(screens: list[dict], rng: random.Random) -> dict:
    weights = [s["weight"] for s in screens]
    return rng.choices(screens, weights=weights, k=1)[0]


class GpuDatabase:
    """Read-only access to the GPU profiles database."""

    def __init__(self):
        self._db = _load_db()

    @property
    def backends(self) -> dict:
        return self._db["backends"]

    @property
    def gpus(self) -> list[dict]:
        return self._db["gpus"]

    def gpus_for_platform(self, platform: str) -> list[dict]:
        vendors = self._db["platform_gpu_mapping"].get(platform, [])
        return [g for g in self._db["gpus"] if g["vendor_prefix"] in vendors]

    def backend(self, name: str) -> dict:
        return self._db["backends"][name]

    def renderer_string(self, gpu: dict) -> str:
        template = self._db["renderer_templates"][gpu["backend"]]
        return template.format(**gpu)

    def vendor_string(self, gpu: dict) -> str:
        return self._db["vendor_strings"][gpu["vendor_prefix"]]

    def hardware_tier(self, tier_name: str) -> dict:
        return self._db["hardware_tiers"][tier_name]

    def screens_for_dpr(self, dpr: float) -> list[dict]:
        key = str(dpr) if dpr != int(dpr) else f"{int(dpr)}.0"
        return self._db["screens"].get(key, self._db["screens"]["1.0"])


class DiversityEngine:
    """Generates coherent, diverse profile parameters.

    All randomness goes through a seeded RNG so profiles are reproducible
    when the same seed is used. When no seed is given, a random one is used.
    """

    def __init__(self, seed: int | None = None):
        self._db = GpuDatabase()
        self._rng = random.Random(seed)

    def generate(
        self,
        *,
        platform: str | None = None,
        gpu_vendor: str | None = None,
        gpu_model: str | None = None,
        cores: int | None = None,
        memory: float | None = None,
        screen: tuple[int, int] | None = None,
        dpr: float | None = None,
    ) -> dict[str, Any]:
        """Generate a coherent set of profile overrides.

        Any parameter that is explicitly passed will be used as-is.
        Everything else is selected randomly with realistic weighting.

        Returns a dict with keys: identity, hardware, webgl, noise, fonts.
        """
        # 1. Platform
        if platform is None:
            platform = self._rng.choice(["Win32", "MacIntel"])

        # 2. GPU selection
        gpu = self._pick_gpu(platform, gpu_vendor, gpu_model)
        backend = self._db.backend(gpu["backend"])
        tier = self._db.hardware_tier(gpu["tier"])

        # 3. Hardware
        if cores is None:
            cores = self._rng.choice(tier["cores"])
        if memory is None:
            memory = self._rng.choice(tier["memory_gb"])
        if dpr is None:
            dpr = self._rng.choice(tier["dpr"])
        if screen is None:
            screens = self._db.screens_for_dpr(dpr)
            s = _weighted_screen(screens, self._rng)
            screen = (s["w"], s["h"])

        # 4. WebGL
        renderer = self._db.renderer_string(gpu)
        vendor = self._db.vendor_string(gpu)

        # Compute extension intersection: backend ∩ swiftshader (what we can
        # actually deliver on server) minus mobile-only extensions
        sw_exts = set(self._db.backend("swiftshader")["extensions"])
        target_exts = set(backend["extensions"])
        effective_exts = sorted(sw_exts & target_exts)
        # Remove mobile-only extensions when spoofing d3d11
        if gpu["backend"] == "d3d11":
            mobile_only = {
                "WEBGL_compressed_texture_astc",
                "WEBGL_compressed_texture_etc",
                "WEBGL_compressed_texture_etc1",
            }
            effective_exts = [e for e in effective_exts if e not in mobile_only]

        # 5. Identity
        identity = self._identity_for_platform(platform)

        # 6. Font pack
        font_pack = {
            "Win32": "windows",
            "MacIntel": "macos",
            "Linux x86_64": "linux",
        }.get(platform, "windows")

        # 7. Noise seeds
        noise = {
            "canvas_seed": f"{self._rng.getrandbits(48):012x}",
            "audio_seed": f"{self._rng.getrandbits(48):012x}",
            "clientrects_seed": f"{self._rng.getrandbits(48):012x}",
            "webgl_seed": f"{self._rng.getrandbits(48):012x}",
        }

        avail_height = screen[1] - self._rng.choice([40, 48, 56, 72])

        return {
            "identity": identity,
            "hardware": {
                "cores": cores,
                "memory": memory,
                "screen_width": screen[0],
                "screen_height": screen[1],
                "avail_width": screen[0],
                "avail_height": avail_height,
                "pixel_ratio": dpr,
                "color_depth": 24,
            },
            "webgl": {
                "vendor": vendor,
                "renderer": renderer,
                "params": dict(backend["params"]),
                "extensions": effective_exts,
                "shader_precision_high": list(backend["shader_precision"]["high_float"]),
                "shader_precision_medium": list(backend["shader_precision"]["medium_float"]),
            },
            "noise": noise,
            "fonts": {"font_pack": font_pack},
        }

    def _pick_gpu(
        self,
        platform: str,
        gpu_vendor: str | None,
        gpu_model: str | None,
    ) -> dict:
        candidates = self._db.gpus_for_platform(platform)
        if not candidates:
            candidates = self._db.gpus

        if gpu_model:
            exact = [g for g in candidates if g["model"] == gpu_model]
            if exact:
                return exact[0]

        if gpu_vendor:
            filtered = [g for g in candidates if g["vendor_prefix"] == gpu_vendor]
            if filtered:
                candidates = filtered

        return _weighted_choice(candidates, self._rng)

    def _identity_for_platform(self, platform: str) -> dict:
        if platform == "Win32":
            return {
                "platform": "Win32",
                "ua_platform": "Windows",
                "ua_platform_version": self._rng.choice(
                    [
                        "15.0.0",
                        "14.0.0",
                        "13.0.0",
                        "10.0.0",
                    ]
                ),
                "ua_arch": "x86",
            }
        elif platform == "MacIntel":
            return {
                "platform": "MacIntel",
                "ua_platform": "macOS",
                "ua_platform_version": self._rng.choice(
                    [
                        "14.5.0",
                        "14.4.1",
                        "14.3.0",
                        "15.0.0",
                        "15.1.0",
                    ]
                ),
                "ua_arch": "arm",
            }
        else:
            return {
                "platform": "Linux x86_64",
                "ua_platform": "Linux",
                "ua_platform_version": "",
                "ua_arch": "x86",
            }


def generate_profile(**kwargs) -> dict[str, Any]:
    """Convenience function: create a DiversityEngine and generate once."""
    engine = DiversityEngine(seed=kwargs.pop("seed", None))
    return engine.generate(**kwargs)
