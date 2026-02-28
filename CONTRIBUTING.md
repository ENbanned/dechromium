# Contributing to dechromium

## Getting started

1. Fork the repository and clone your fork
2. Create a virtual environment and install dev dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[server]"
pip install --group dev
pre-commit install
```

## Making changes

1. Create a branch from `main`:

```bash
git checkout -b feat/my-feature
```

2. Make your changes
3. Run checks:

```bash
ruff check src/
ruff format src/
pytest
```

4. Commit using [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: correct bug in profile creation
docs: update installation guide
```

5. Push and open a Pull Request against `main`

## Code style

- Enforced by ruff (config in `pyproject.toml`)
- Line length: 99
- `from __future__ import annotations` in every module
- Private modules prefixed with `_`
- Pydantic v2 for models, StrEnum for enums

## Project layout

```
src/dechromium/     # Main package
  models/           # Pydantic models
  profile/          # Profile management and launcher
  browser/          # Browser pool and process lifecycle
  server/           # Optional FastAPI REST API
patches/            # Chromium patches by version
build/              # Patch management scripts
docs/               # mkdocs-material documentation
```
