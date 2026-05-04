# External Integrations

**Analysis Date:** 2026-05-04

## APIs & External Services

LicitaIA is an **offline, self-contained desktop/web app**. It does not call any external HTTP API at runtime. All "integrations" are local files, embedded engines, or browser-side asset fetches.

**Embedded rules engine:**
- CLIPS (via `clipspy`) — In-process expert system used for technical alerts. Loaded by `src/reglas/alertas_clips.py:generar_alertas_tecnicas`. Runs entirely in-memory via `clips.Environment()`; no daemon, no network, no persistence.
  - SDK/Client: `clipspy>=1.0.6,<2.0` (PyPI).
  - Auth: Not applicable (in-process).
  - Knowledge base: Embedded as Python strings in `src/reglas/templates.py` (`TEMPLATES`, `RULES`).

**Browser-side asset CDN (UI only):**
- Google Fonts — `Inter` font family fetched by the user's browser at page load. Configured in `.streamlit/config.toml:6` (`font = "Inter:https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap, sans-serif"`). The Python backend never calls Google Fonts; only the rendered HTML embeds the URL.

**No third-party SDKs detected:**
- No Stripe / Supabase / AWS / GCP / Azure / Firebase / Sentry / Algolia clients in `src/` or `pages/`.
- No `requests` / `httpx` / `aiohttp` / `urllib3` imports anywhere in the source (only `urllib.request` inside the Dockerfile healthcheck shell command).

## Data Storage

**Databases:**
- SQLite 3 (single-file embedded DB) — Sole datastore.
  - File: `data/precios.db` (force-tracked in git via `.gitignore:38` `!data/precios.db`).
  - Connection: `src/infraestructura/db/connection.py:conectar()` context manager.
  - PRAGMAs enforced on every connection: `foreign_keys = ON`, `journal_mode = WAL`.
  - Driver: `sqlite3` (Python stdlib). No ORM.
  - Schema: 26 whitelisted tables (`src/infraestructura/db/connection.py:_TABLAS_PERMITIDAS`) covering price catalogs (`tuberias`, `acerados`, `bordillos`, `calzadas`, `pozos`, `entibacion`, `valvuleria`, `demolicion`, `subbases`, `desmontaje`, `imbornales`, `acometidas`, `excavacion`, `acometida_defecto`, `pozos_existentes_precios`, `espesores_calzada`, `defaults_ui`, `config`) and budget history (`presupuestos`, `presupuesto_capitulos`, `presupuesto_partidas`, `presupuesto_parametros`, `presupuesto_trazabilidad`).
  - Storage convention: prices stored as `INTEGER` cents (Migration 13 — `src/infraestructura/db/migrations/m13_integer_centimos.py`). Conversion `_cents_a_eur` / `_eur_a_cents` in `src/infraestructura/db_precios.py:44-51`.
  - Migrations: idempotent forward-only chain M01–M16 in `src/infraestructura/db/migrations/`, dispatched by `src/infraestructura/db/runner.py:init_db`. Tracked in `schema_version` table.
  - WAL side-files (`*.db-wal`, `*.db-shm`) ignored via `.gitignore:32-33`.

**File Storage:**
- Local filesystem only. No object-storage SDK present.
- Static asset: `data/static/cropped-Logo_2024-300x300.png` (logo).
- Reference catalog: `data/catalogo_oficial.json` — JSON snapshot of EMASESA-validated prices (with `pct_ci=1.05` applied) used by `src/infraestructura/validacion_oficial.py:detectar_drifts` to flag drift between editor catalog and the audited Excel source.
- Source spreadsheet: `240415_VALORACIÓN ACTUACIONES.xlsx` at repo root — kept as the authoritative EMASESA valuation reference. Not consumed at runtime (no `openpyxl`/`pandas.read_excel` import). Excluded from Docker image via `.dockerignore:42-43`.

**Caching:**
- In-process memoization via `@st.cache_data` in `src/ui/precios_cache.py` (Streamlit's data cache). Wraps `src.infraestructura.precios.cargar_precios`. Invalidation handled by Streamlit's TTL/file-watch heuristics; no Redis/Memcached.

## Authentication & Identity

**Auth Provider:**
- None. The application has no login, no user accounts, no session identity. All Streamlit sessions are anonymous and equal-privilege.
- The "admin" page (`pages/admin_precios.py`) is reachable by anyone who can open the Streamlit app — protection is purely deployment-level (network ACL / Streamlit Cloud sharing settings).

**Streamlit secrets store:**
- `.streamlit/secrets.toml` is git-ignored (`.gitignore:26`) and dockerignored (`.dockerignore:58`), but no code reads `st.secrets` today. The slot exists for future use.

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry / Rollbar / Bugsnag SDK installed. Errors surface via Streamlit's default red error boxes (`st.error(...)` calls in `pages/calculadora.py:35`, `pages/admin_precios.py:28`) and Python tracebacks in the server log.

**Logs:**
- Python stdlib `logging`, configured globally in `app_licitaia.py:21-25` at `DEBUG` level.
- Format: `%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s`.
- Output: stdout (`PYTHONUNBUFFERED=1` in Dockerfile, no log file rotation, no log shipper).
- Per-module loggers via `logger = logging.getLogger(__name__)` in every `src/**/*.py` file that emits diagnostics.
- User-memory note (`feedback_testing_strategy.md`) treats logs as a primary diagnostic surface — preserve them when refactoring.

**Health checks:**
- Container-level only. `Dockerfile:37-38` runs `python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)"` every 30 s. Streamlit serves `/_stcore/health` natively.

## CI/CD & Deployment

**Hosting:**
- Streamlit Community Cloud (referenced explicitly in `src/infraestructura/db/connection.py:42-45` and `.gitignore:34-37` — DB is force-tracked because Cloud needs it at boot since `init_db()` only creates empty tables).
- Docker container (Dockerfile present) — alternative deployment path, exposes port 8501.

**CI Pipeline:**
- None checked in. `.github/` exists but contains only `.github/instructions/` (gitignored Codacy notes per `.gitignore:75`). There is no `.github/workflows/` directory and no `.gitlab-ci.yml` / `.circleci/` / `azure-pipelines.yml`.
- Tests run manually via `pytest tests/ -v` (per `tests/conftest.py` docstring).

**Container registry:**
- `Dockerfile:5` declares `org.opencontainers.image.source=https://github.com/LuciaM13/licitaIA`. No registry push automation in-tree.

## Environment Configuration

**Required env vars:**
- None at application level. The app reads zero `os.environ` keys in `src/`.
- Dockerfile sets only Python/pip behavior toggles (`PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `PIP_NO_CACHE_DIR`, `PIP_DISABLE_PIP_VERSION_CHECK`).

**Secrets location:**
- `.streamlit/secrets.toml` (slot reserved, currently absent and git-ignored). No `.env` file present.

**Effective configuration sources (in priority order):**
1. SQLite `config` table (`data/precios.db`) — runtime tunables (e.g. `pct_ci`, `pct_gg`, `pct_bi`, `pct_iva`). Loaded via `src/infraestructura/db_precios.py:cargar_todo`.
2. `.streamlit/config.toml` — UI theme only.
3. `data/catalogo_oficial.json` — reference snapshot of the EMASESA Excel for drift detection.
4. Streamlit CLI flags in `Dockerfile:40-44` — server bind, port, headless mode, telemetry off.

## Webhooks & Callbacks

**Incoming:**
- None. No HTTP routes are defined beyond Streamlit's built-in pages and its `/_stcore/*` internal endpoints. No FastAPI / Flask / Django app present.

**Outgoing:**
- None. No HTTP client code emits requests at runtime.

## External Reference Inputs (manual workflow)

These are not code integrations but are load-bearing for the TFG validation workflow and worth noting for future integrators:

- **EMASESA Excel valuation** (`240415_VALORACIÓN ACTUACIONES.xlsx`) — authoritative source for prices. Drives Migrations M01–M16 and is validated against by `tests/test_validacion_excel.py` and `tests/test_snapshot_excel.py`.
- **BC3 budget files** (referenced in user memory `feedback_validacion_sin_restar_fuera_alcance.md` and `feedback_validacion_parametros_derivados.md`) — used externally to compare LicitaIA outputs against industry-standard tender exports. No BC3 parser exists in the codebase today; comparison is currently manual.
- **CLIPS rule sources** — derived from the EMASESA Excel (technical) + LSP Ley 9/2017 (administrative) + complementary regulations (`project_fuentes_reglas_se.md`). Citations live in the `fuente` slot of each fact emitted by `src/reglas/templates.py`.

---

*Integration audit: 2026-05-04*
