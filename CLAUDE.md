# CLAUDE.md — dechromium

## Project overview

dechromium is an open-source anti-detect browser library for Python. It manages Chromium browser profiles with spoofed fingerprints (navigator, screen, WebGL, canvas, audio, fonts, network) via a patched Chromium binary controlled through `--aspect-*` command-line flags.

- **GitHub**: ENbanned/dechromium
- **PyPI**: `dechromium`
- **License**: MIT
- **Python**: 3.11+

For the full build workspace reference (Chromium checkout, cross-compilation, build workflow), see `/root/development/BROWSER/CLAUDE.md`.

## Repo structure

```
src/dechromium/          # Main package (src/ layout)
  __init__.py            # Public API exports
  _cli.py                # CLI entry point (dechromium command)
  _client.py             # Dechromium class — main user-facing API
  _config.py             # Config model (data_dir, browser_bin, fonts_dir)
  _installer.py          # BrowserManager — download/update/manage Chromium installations
  _exceptions.py         # Exception hierarchy
  models/                # Pydantic v2 models (Profile, Identity, Hardware, etc.)
  profile/               # Profile management, launcher, fontconfig
  browser/               # Browser pool, process lifecycle, cookies
  server/                # Optional FastAPI REST API
  data/                  # Static data (gpu_profiles.json)
patches/                 # Chromium patches organized by version
  145.0.7632.116/        # 001-aspect-infrastructure.patch through 010-font-control.patch
build/                   # Build + patch management scripts
  build_chromium.py      # Multi-platform Chromium build (linux/win/all)
  package.py             # Package built Chromium into release archives
  release.py             # Upload to GitHub Releases via gh CLI
  apply_patches.sh       # Apply patches to chromium/src
  export_patches.sh      # Export aspect branch commits as patches
  new_patch.sh           # Create a new numbered patch
  edit_patch.sh          # Edit an existing patch
  build.sh               # Legacy Linux-only build script
docs/                    # mkdocs-material documentation
fonts/                   # TTF font files for font isolation
.github/workflows/       # CI, release, docs workflows
```

## Dev setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[server]"
pip install --group dev
pre-commit install
```

## Code standards

- **Formatter/linter**: ruff (line-length 99, target py311)
- **Lint rules**: E, F, I, UP, B, SIM, RUF
- **Layout**: src/ layout with `_` prefix for private modules (public API in `__init__.py`)
- **Models**: Pydantic v2 BaseModel, StrEnum for enums
- **Type hints**: required on all public functions, `py.typed` marker present
- **Imports**: `from __future__ import annotations` in every module
- **Cross-platform**: Use `sys.platform == "win32"` guards for Windows-specific behavior. Binary name: `chrome` (Linux/macOS), `chrome.exe` (Windows). Skip fontconfig XML and DISPLAY/Xvfb on Windows.

## Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`

Scope is optional. Examples:
- `feat: add install command for Chromium downloads`
- `fix: correct proxy auth handling for SOCKS5`
- `docs: update quickstart guide`
- `ci: add Python 3.13 to test matrix`

## Branching

- `main` is the release branch — always deployable
- Feature branches off `main`, merged via PR
- Branch naming: `feat/short-description`, `fix/short-description`

## When to commit

- One logical change per commit
- Commit message explains WHY, not WHAT (the diff shows what)
- Run `ruff check src/` and `ruff format --check src/` before committing

## Release process (library)

1. Bump version in `pyproject.toml` and `src/dechromium/__init__.py`
2. Update `CHANGELOG.md`
3. Commit: `chore: release v0.X.0`
4. Tag: `git tag v0.X.0`
5. Push: `git push origin main --tags`
6. `release.yml` publishes to PyPI via Trusted Publishers

## Release process (Chromium)

1. Build patched Chromium for all platforms:
   ```bash
   python build/build_chromium.py --platform all
   ```
2. Package:
   ```bash
   python build/package.py --version VERSION --platform all
   ```
3. Release:
   ```bash
   python build/release.py --version VERSION          # or --draft for testing
   ```

This creates a GitHub Release tagged `chromium-VERSION` with:
- `dechromium-chromium-VERSION-linux-x64.tar.gz`
- `dechromium-chromium-VERSION-win-x64.tar.gz`
- `manifest.json` — per-platform SHA-256 hashes, patch list, min_library

`manifest.json` example:
```json
{
  "chromium_version": "145.0.7632.116",
  "min_library": "0.3.0",
  "patches": ["001-aspect-infrastructure", "002-navigator-spoofing", "..."],
  "assets": {
    "linux-x64": {"sha256": "...", "archive": "dechromium-chromium-145.0.7632.116-linux-x64.tar.gz"},
    "win-x64": {"sha256": "...", "archive": "dechromium-chromium-145.0.7632.116-win-x64.tar.gz"}
  }
}
```

### How `dechromium install` works

- `dechromium install` → queries GitHub Releases API → finds latest `chromium-*` tag → downloads
- `dechromium install 146.x.x.x` → fetches that specific release from GitHub
- **No hardcoded version list** — the library talks to GitHub API, not to internal constants
- If `manifest.json` is present in the release → checks `min_library` before downloading, verifies `sha256` after
- Browsers stored in `~/.dechromium/browsers/<version>/chrome[.exe]` (multi-version side-by-side)
- Default browser = latest installed version (auto-resolved by `Config`)

### Hotfix for an existing Chromium version

If a patch is fixed and the binary is re-uploaded to the same GitHub Release:
- `dechromium update` detects it via `asset.updated_at` timestamp comparison
- Re-downloads and replaces the local installation

### When to update the library after a new Chromium release

- **Same `--aspect-*` flags** → no library update needed. Just create the GitHub Release.
- **New `--aspect-*` flag added** → library needs updating (new model fields in `models/`, new args in `profile/_launcher.py`). Bump minor version.
- **Flag removed or renamed** → breaking change, library major version bump.

### Browser management CLI

```
dechromium install [VERSION] [--force]   Download and install browser
dechromium update                        Check for updates to installed browsers
dechromium browsers                      List available and installed browsers
dechromium uninstall VERSION             Remove installed browser
```

## Chromium version contract

The interface between the library and Chromium is the set of `--aspect-*` flags in `profile/_launcher.py`.

## Porting patches to new Chromium

```bash
# In the chromium/src checkout:
git fetch --tags
git checkout NEW_VERSION_TAG
git cherry-pick <patch-commits>   # or rebase the aspect branch
# Fix conflicts, test, then export:
cd /path/to/dechromium
bash build/export_patches.sh
```

Patches are numbered `001-name.patch` through `NNN-name.patch` under `patches/VERSION/`.

## CI/CD

| Workflow | Trigger | Action |
|----------|---------|--------|
| `ci.yml` | push/PR to main | ruff lint + format check, pytest on 3.11/3.12/3.13 |
| `release.yml` | `v*` tag push | build + publish to PyPI |
| `docs.yml` | push to main | mkdocs gh-deploy |

## Testing

```bash
pytest                   # run all tests
pytest tests/ -v         # verbose
```

## Documentation

- Built with mkdocs-material
- Source in `docs/`
- Config in `mkdocs.yml`
- Auto-deploys to GitHub Pages on push to main

## Pre-commit hooks

Configured in `.pre-commit-config.yaml`:
- trailing-whitespace, end-of-file-fixer, check-yaml, check-toml, check-merge-conflict, check-added-large-files
- ruff (lint with --fix)
- ruff-format

Bypass if needed: `git commit --no-verify` (use sparingly)
