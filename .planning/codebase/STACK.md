# Technology Stack

**Analysis Date:** 2026-05-04

## Languages

**Primary:**
- Python 3.11 — All application, domain, and rules code (`src/`, `pages/`, `app_licitaia.py`, `tests/`).
- CLIPS (rule language, embedded as strings) — Expert-system rule base in `src/reglas/templates.py`. Loaded at runtime via `clipspy` from `src/reglas/alertas_clips.py`.

**Secondary:**
- SQL (SQLite dialect) — Schema DDL in `src/infraestructura/db/schema.py`, seed data in `data/precios_seed.sql`, migrations in `src/infraestructura/db/migrations/m01_*.py … m16_*.py`.
- TOML — Streamlit config in `.streamlit/config.toml`.
- JSON — Reference catalog in `data/catalogo_oficial.json`.

## Runtime

**Environment:**
- Python 3.11 (pinned via `Dockerfile`: `FROM python:3.11-slim`).
- Local development uses Conda env `licitaia` (referenced in `tests/conftest.py` comment: `conda activate licitaia`).

**Package Manager:**
- pip (`PIP_NO_CACHE_DIR=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1` set in Dockerfile).
- Lockfile: not present (no `requirements.lock`, no `Pipfile.lock`, no `poetry.lock`). Versions are pinned via `>=X,<Y` upper bounds in `requirements.txt`.

## Frameworks

**Core:**
- `streamlit>=1.38,<2.0` — UI framework. Multipage navigation via `st.navigation` (≥1.36) and `st.logo` (≥1.37). Entrypoint: `app_licitaia.py`. Pages in `pages/calculadora.py`, `pages/historial.py`, `pages/admin_precios.py`.
- `clipspy>=1.0.6,<2.0` — Python bindings to the CLIPS expert-system shell. Sole consumer: `src/reglas/alertas_clips.py`. Builds `clips.Environment()` per call, loads templates/rules from `src/reglas/templates.py`.
- `pandas>=2.0,<3.0` — DataFrames used by the price-admin editor (`pages/admin_precios.py`) and the calculator page (`pages/calculadora.py`).

**Testing:**
- `pytest>=8.0,<9.0` — Sole test runner. Configuration via `tests/conftest.py` (sets cwd, calls `init_db()` once). User memory note (`feedback_testing_strategy.md`) flags that the official integration strategy is `streamlit.testing.AppTest`, not unit-style pytest — but pytest is still the executor.
- 21 test modules under `tests/` (e.g. `test_validacion_excel.py`, `test_snapshot_excel.py`, `test_bd_invariante_ci.py`, `test_calculadora.py`, `test_historial.py`).

**Build/Dev:**
- Docker (multi-stage build defined in `Dockerfile`) — Builds slim Python image, installs `build-essential`/`gcc` only to compile `clipspy` wheels, then purges them. Runs as non-root user `licitaia` on port 8501.
- HEALTHCHECK uses `urllib.request` against Streamlit's `/_stcore/health` endpoint (`Dockerfile:38`).
- No CI pipeline checked into the repo: `.github/` exists but contains only `.github/instructions/` (gitignored Codacy notes); there is no `.github/workflows/` directory.

## Key Dependencies

**Critical (runtime, from `requirements.txt`):**
- `streamlit>=1.38,<2.0` — Whole UI, session state, caching (`@st.cache_data` consumed in `src/ui/precios_cache.py`), theming.
- `pandas>=2.0,<3.0` — Tabular display/editing of catalogs.
- `clipspy>=1.0.6,<2.0` — Expert-system runtime (CLIPS bindings). Critical for "Pata 2" of the TFG defense.

**Critical (dev, from `requirements-dev.txt`):**
- `pytest>=8.0,<9.0` — Test runner.

**Standard library (load-bearing):**
- `sqlite3` — Sole DB driver. Used in `src/infraestructura/db/connection.py` (context manager `conectar()`), `src/infraestructura/db_precios.py`, `src/aplicacion/historial.py`. WAL mode + `PRAGMA foreign_keys=ON`.
- `dataclasses` — Domain models (`src/domain/parametros.py:ParametrosProyecto`, `src/domain/financiero.py`).
- `logging` — Configured globally at DEBUG in `app_licitaia.py:21-25`. User memory (`feedback_testing_strategy.md`) flags logging as a first-class diagnosis tool.
- `pathlib`, `contextlib`, `typing`, `unicodedata`, `math`, `json`, `copy` — Used across `src/`.

**Infrastructure / packaging:**
- No ORM (raw SQL via `sqlite3`).
- No HTTP client library (no `requests`/`httpx`/`urllib3` imports outside the Dockerfile healthcheck stdlib `urllib.request`).
- No `python-docx` / `openpyxl` despite the presence of `240415_VALORACIÓN ACTUACIONES.xlsx`. The "Word export" (`src/infraestructura/utils.py:78` `generar_texto_word`) emits plain text, not a `.docx` document.

## Configuration

**Environment:**
- No `.env`, `.env.*`, or `os.environ`-driven config detected in `src/`. Configuration is data-driven (rows in the `config` table inside `data/precios.db`) rather than environment-driven.
- `.streamlit/secrets.toml` is git-ignored (`.gitignore:26`) and dockerignored (`.dockerignore:58`); not present in the working tree.
- `.gitignore` also ignores `.env`/`*.env` (`.dockerignore:59-60`), so any future env-based secrets will be honored, but none are wired today.

**Build:**
- `Dockerfile` — Single-file image build. ENV vars: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `PIP_NO_CACHE_DIR=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1`.
- `.dockerignore` — Excludes tests, `*.xlsx`, `*.md`, `.claude/`, `.streamlit/secrets.toml`, `*.tar`, IDE configs, and DB backup files.
- `.streamlit/config.toml` — Theme only (EMASESA brand: green `#97D700`, cyan `#00A9E0`, Inter font from Google Fonts CDN). No server config baked in (server flags are passed via `CMD` in the Dockerfile: `--server.address=0.0.0.0 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false`).
- Runtime data layout: SQLite DB at `data/precios.db` (path computed from package location in `src/infraestructura/db/connection.py:20`), static logo at `data/static/cropped-Logo_2024-300x300.png`, official-price reference at `data/catalogo_oficial.json`.

**App-level config:**
- Logging configured globally at DEBUG in `app_licitaia.py:21` (TODO note in source: switch to INFO for production).
- Page config (`st.set_page_config`) and global CSS injection (`src/ui/theme.py:inject_global_styles`) executed once in `app_licitaia.py:34-40`.
- Schema migrations registered in `src/infraestructura/db/migrations/__init__.py:MIGRACIONES` (M01 … M16) and dispatched idempotently by `src/infraestructura/db/runner.py:init_db`.

## Platform Requirements

**Development:**
- Python 3.11 + Conda env `licitaia` (per `tests/conftest.py` docstring).
- C toolchain (`gcc`, `build-essential`) only required if PyPI does not provide a `clipspy` wheel for the target arch. On Windows dev (current host: Win11), pre-built wheels are usually available.
- Disk: SQLite DB lives in-tree at `data/precios.db` and is force-versioned (`.gitignore:38` whitelists it via `!data/precios.db`).

**Production:**
- Streamlit Community Cloud (referenced in `src/infraestructura/db/connection.py:42-45` — WAL mode is needed there for tab-concurrency) **or** Docker container exposing port 8501 (Dockerfile target).
- Container runs as non-root user `licitaia` with ownership of `/app` so it can write to `data/` (DB writes from admin page).
- Healthcheck: HTTP GET on `localhost:8501/_stcore/health` every 30 s.

---

*Stack analysis: 2026-05-04*
