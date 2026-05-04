# Codebase Structure

**Analysis Date:** 2026-05-04

## Directory Layout

```
licitaIA/
├── app_licitaia.py                    # Streamlit entrypoint (init_db + navigation)
├── Dockerfile                         # python:3.11-slim image, CMD streamlit run
├── requirements.txt                   # Runtime deps
├── requirements-dev.txt               # Test/dev deps
├── 240415_VALORACIÓN ACTUACIONES.xlsx # Reference Excel (EMASESA valoración)
│
├── pages/                             # Streamlit pages (declared in st.navigation)
│   ├── calculadora.py                 # Budget computation form + result
│   ├── historial.py                   # Saved-budget browser
│   └── admin_precios.py               # Catalogue editor
│
├── src/
│   ├── __init__.py
│   │
│   ├── domain/                        # Pure core (no streamlit / clips / sqlite3)
│   │   ├── __init__.py
│   │   ├── parametros.py              # `ParametrosProyecto` dataclass
│   │   ├── tipos.py                   # `ItemCatalogo`, `Precios`, `ResultadoPresupuesto`
│   │   ├── constantes.py              # `PCT_CI_DEFAULT`, `NULL_SENTINEL`, tolerances
│   │   ├── financiero.py              # `calcular_resumen` (PEM → GG/BI/IVA/TOTAL)
│   │   ├── geometria.py               # Trench geometry (`GeometriaZanja`)
│   │   └── reglas/
│   │       ├── elegibilidad.py        # Eligibility predicates
│   │       └── desempates.py          # Tiebreak / ranking functions
│   │
│   ├── presupuesto/                   # Chapter assembly (no streamlit / clips / sqlite3)
│   │   ├── bloques.py                 # `ensamblar_*` orchestrators
│   │   ├── capitulos_obra_civil.py    # Civil works chapters
│   │   ├── capitulos_superficie.py    # Surface (paving / demolition) chapters
│   │   └── materiales.py              # Supply partidas (excluded from GG/BI)
│   │
│   ├── reglas/                        # Reasoning (only alertas_clips imports clips)
│   │   ├── decisor.py                 # Deterministic decisor (Python pure)
│   │   ├── alertas_clips.py           # CLIPS adapter — sole CLIPS importer
│   │   ├── templates.py               # CLIPS deftemplate/defrule sources + thresholds
│   │   ├── explicaciones.py           # Spanish explanations of decisions
│   │   └── normalizacion.py           # Input normalisation + factor_piezas table
│   │
│   ├── aplicacion/                    # Use cases (no streamlit)
│   │   ├── calcular_presupuesto.py    # Budget computation orchestration
│   │   ├── editar_catalogo.py         # Admin save flow (validate + diff + drift)
│   │   ├── historial.py               # CRUD for saved budgets
│   │   └── contratos.py               # TypedDict contracts (ResultadoPreparacion, …)
│   │
│   ├── infraestructura/               # Adapters (no streamlit)
│   │   ├── precios.py                 # Public load/save/aplicar_ci
│   │   ├── db_precios.py              # CRUD over catalogue tables
│   │   ├── diff_precios.py            # Edit-time diff
│   │   ├── validacion_oficial.py      # Drift vs catalogo_oficial.json
│   │   ├── utils.py                   # `euro`, `find_by_label`, validar_parametros, …
│   │   └── db/
│   │       ├── connection.py          # `conectar()` ctxmgr + DB_PATH + whitelist
│   │       ├── schema.py              # Initial DDL `_SCHEMA`
│   │       ├── runner.py              # `init_db` + migration dispatcher
│   │       ├── helpers.py             # `_rows_to_dicts`, `_cargar_por_red`
│   │       └── migrations/
│   │           ├── __init__.py        # `MIGRACIONES` declarative list
│   │           └── m01..m16_*.py      # 16 versioned migrations
│   │
│   └── ui/                            # Streamlit-aware helpers
│       ├── precios_cache.py           # `@st.cache_data` wrapper over cargar_precios
│       ├── inputs.py                  # Re-usable form widgets (tubería, subbase)
│       ├── materiales.py              # Demolition material selector helpers
│       ├── theme.py                   # Corporate CSS injection (EMASESA palette)
│       └── session/
│           └── claves.py              # st.session_state key constants
│
├── data/
│   ├── precios.db                     # Production SQLite store
│   ├── precios_seed.sql               # Initial seed
│   ├── catalogo_oficial.json          # Reference for drift detection
│   └── static/                        # Logo, etc.
│
├── notebook/                          # Auxiliary Excel exploration / TFG outputs
│   ├── 08_validacion_excel.ipynb
│   ├── _excel_helpers.py
│   ├── _inspeccion_excel.py
│   ├── resultados_tfg.docx
│   └── resultados_tfg.md
│
└── tests/                             # AppTest + structural invariant tests
    ├── conftest.py
    ├── helpers.py
    ├── test_fronteras_capas.py        # AST-tested layer fences
    ├── test_reglas_estructura.py      # CLIPS-only-in-alertas_clips invariant
    ├── test_aplicacion_estructura.py  # Use case contracts
    ├── test_tipos_domain.py
    ├── test_constantes_dominio.py
    ├── test_db_estructura.py
    ├── test_bd_invariante_ci.py       # BD × pct_ci ≈ Excel oficial
    ├── test_validacion_excel.py
    ├── test_snapshot_excel.py
    ├── test_calculadora.py
    ├── test_admin.py
    ├── test_historial.py
    ├── test_historial_snapshot.py
    ├── test_etiquetas.py              # CLIPS labels
    ├── test_audit.py
    ├── test_fail_fast_precios.py
    └── test_infraestructura_pura.py
```

## Directory Purposes

**`pages/`:**
- Purpose: Streamlit page modules registered with `st.navigation` in `app_licitaia.py:44-48`.
- Contains: one file per top-level page; each is run as a script on each rerun.
- Key files: `pages/calculadora.py`, `pages/historial.py`, `pages/admin_precios.py`.

**`src/domain/`:**
- Purpose: pure domain core — types, parameters, constants, pure formulas, pure rule predicates.
- Contains: dataclasses, TypedDicts, frozen constants, math.
- Key files: `src/domain/parametros.py`, `src/domain/tipos.py`, `src/domain/financiero.py`, `src/domain/geometria.py`, `src/domain/constantes.py`, `src/domain/reglas/elegibilidad.py`, `src/domain/reglas/desempates.py`.

**`src/presupuesto/`:**
- Purpose: assemble chapters from parameters + decisions + resolved items.
- Contains: orchestrators (`bloques.py`) and per-chapter functions.
- Key files: `src/presupuesto/bloques.py`, `src/presupuesto/capitulos_obra_civil.py`, `src/presupuesto/capitulos_superficie.py`, `src/presupuesto/materiales.py`.

**`src/reglas/`:**
- Purpose: deterministic decisor + CLIPS-based alerter + explanations.
- Contains: `decisor.py` (no CLIPS), `alertas_clips.py` (only CLIPS importer), `templates.py` (CLIPS DSL strings), `explicaciones.py`, `normalizacion.py`.
- Key files: `src/reglas/decisor.py`, `src/reglas/alertas_clips.py`, `src/reglas/templates.py`.

**`src/aplicacion/`:**
- Purpose: use cases that orchestrate domain + infrastructure for one user flow.
- Contains: one file per use case + `contratos.py` for TypedDict contracts.
- Key files: `src/aplicacion/calcular_presupuesto.py`, `src/aplicacion/editar_catalogo.py`, `src/aplicacion/historial.py`, `src/aplicacion/contratos.py`.

**`src/infraestructura/`:**
- Purpose: adapters to SQLite, Excel-oficial cross-validation, and formatting helpers.
- Contains: top-level modules (`precios.py`, `db_precios.py`, `diff_precios.py`, `validacion_oficial.py`, `utils.py`) and the `db/` sub-package.
- Key files: `src/infraestructura/precios.py`, `src/infraestructura/db/connection.py`, `src/infraestructura/db/runner.py`, `src/infraestructura/db/migrations/__init__.py`.

**`src/infraestructura/db/migrations/`:**
- Purpose: idempotent versioned migrations.
- Contains: one file per migration `m01_..` … `m16_..`, each exposing `VERSION`, `DESCRIPCION`, `aplicar(conn)`.
- Key files: `src/infraestructura/db/migrations/__init__.py` (declares `MIGRACIONES` order — note M7 before M6 by design).

**`src/ui/`:**
- Purpose: anything that touches Streamlit at module scope.
- Contains: cached price loader, widgets, theming, session-state keys.
- Key files: `src/ui/precios_cache.py`, `src/ui/inputs.py`, `src/ui/materiales.py`, `src/ui/theme.py`, `src/ui/session/claves.py`.

**`data/`:**
- Purpose: persistent data and reference artefacts.
- Contains: SQLite DB, seed SQL, official Excel catalogue extract, static logo.
- Note: `data/precios.db` is committed and is the runtime store.

**`notebook/`:**
- Purpose: exploratory / TFG-output material; not imported by runtime code.
- Contains: Jupyter notebook + Excel helpers + TFG results document.
- Generated: yes (notebook outputs).
- Committed: yes.

**`tests/`:**
- Purpose: AppTest-driven flow tests + structural / invariant tests.
- Contains: `conftest.py`, `helpers.py`, plus `test_*.py` files. AST-based architectural tests live in `tests/test_fronteras_capas.py` and `tests/test_reglas_estructura.py`.

## Key File Locations

**Entry Points:**
- `app_licitaia.py`: Streamlit entrypoint — runs `init_db()`, sets page config, declares navigation.
- `pages/calculadora.py`: budget computation page.
- `pages/historial.py`: saved-budget browser.
- `pages/admin_precios.py`: catalogue editor.
- `src/infraestructura/db/runner.py`: `init_db()` (called at app boot).

**Configuration:**
- `Dockerfile`: container image.
- `requirements.txt` / `requirements-dev.txt`: dependencies.
- `data/precios.db`: runtime configuration values live in the `config` table inside the DB (`pct_gg`, `pct_bi`, `pct_iva`, `pct_ci`, …).
- `src/domain/constantes.py`: hard-coded invariants (`PCT_CI_DEFAULT`, tolerances, `NULL_SENTINEL`).
- `src/reglas/templates.py`: CLIPS thresholds (`UMBRALES` dict) — edit here to change alert thresholds, never inside the rule strings.

**Core Logic:**
- `src/aplicacion/calcular_presupuesto.py`: budget orchestration use case.
- `src/reglas/decisor.py`: deterministic material selection.
- `src/reglas/alertas_clips.py`: CLIPS-based technical alerts.
- `src/presupuesto/bloques.py`: chapter assembly.
- `src/domain/financiero.py`: financial summary formulas.
- `src/domain/geometria.py`: trench geometry formulas.

**Persistence:**
- `src/infraestructura/db/connection.py`: `conectar()` context manager + `DB_PATH` + whitelist.
- `src/infraestructura/db/schema.py`: initial DDL.
- `src/infraestructura/db/runner.py`: migration dispatcher.
- `src/infraestructura/db/migrations/m*.py`: versioned migrations.
- `src/infraestructura/db_precios.py`: catalogue CRUD (`cargar_todo`, `guardar_todo`).

**Testing:**
- `tests/conftest.py`: shared fixtures.
- `tests/helpers.py`: helper builders.
- `tests/test_fronteras_capas.py`: layer-boundary AST tests (architectural invariants).
- `tests/test_reglas_estructura.py`: enforces CLIPS-only-in-`alertas_clips`.
- `tests/test_aplicacion_estructura.py`: use case contract tests.

## Naming Conventions

**Files:**
- `snake_case.py` everywhere.
- Migrations: `m{NN:02d}_{snake_descripcion}.py` (e.g. `m13_integer_centimos.py`).
- Test files: `test_{area}.py` (e.g. `test_calculadora.py`, `test_fronteras_capas.py`).
- Modules with deliberately Spanish names match the domain vocabulary used by EMASESA (`presupuesto`, `valvuleria`, `imbornales`, `entibacion`).

**Directories:**
- `snake_case`, Spanish where the concept is domain-specific (`presupuesto`, `aplicacion`, `infraestructura`, `reglas`).
- `domain` and `db` kept in English as conventional architecture terms.
- Sub-packages use `__init__.py` and re-export public names (e.g. `src/infraestructura/db/__init__.py:21-30`).

**Functions:**
- `snake_case`, Spanish for domain (`calcular_presupuesto`, `ensamblar_obra_civil_aba`, `desempatar_entibacion`).
- Internal helpers prefixed with `_` (`_acumular`, `_resolver_item_ci`, `_aplicar_overrides`).

**Constants:**
- `UPPER_SNAKE_CASE` (`PCT_CI_DEFAULT`, `NULL_SENTINEL`, `MIGRACIONES`, `_TABLAS_PERMITIDAS`, `FACTORES_PIEZAS`).
- Module-private constants prefixed with `_`.

**TypedDict / dataclasses:**
- `PascalCase` (`ParametrosProyecto`, `ResumenFinanciero`, `GeometriaZanja`, `ItemCatalogo`, `Precios`, `ResultadoPreparacion`).

## Where to Add New Code

**New use case (e.g. "exportar a Word", "simular escenarios"):**
- Primary code: `src/aplicacion/{nombre_use_case}.py`.
- Contracts: extend `src/aplicacion/contratos.py` (or split into `contratos_{contexto}.py` if it grows; see policy in the docstring at `src/aplicacion/contratos.py:11-18`).
- Page: new file under `pages/` registered in `app_licitaia.py:44`.
- Tests: `tests/test_{use_case}.py`.

**New chapter / partida calculation:**
- Pure math: a new function in `src/presupuesto/capitulos_obra_civil.py` or `capitulos_superficie.py` returning `(subtotal, partidas)` or `None`.
- Wire it into the relevant `ensamblar_*` in `src/presupuesto/bloques.py` via `_acumular`.
- If geometry is involved: extend `src/domain/geometria.py`.
- Tests: extend `tests/test_calculadora.py` and snapshot in `tests/test_snapshot_excel.py`.

**New CLIPS rule / alert:**
- Append a `(defrule …)` block to the rule strings in `src/reglas/templates.py`.
- Add any new threshold to `UMBRALES` in the same file (do not hard-code in the rule string).
- Do **not** create a new module that imports `clips`; the architectural test forbids it.
- Tests: `tests/test_etiquetas.py`.

**New deterministic decision rule:**
- Eligibility predicate: `src/domain/reglas/elegibilidad.py`.
- Tiebreak: `src/domain/reglas/desempates.py`.
- Wire into `src/reglas/decisor.py::resolver_decisiones`.
- Generate explanation in `src/reglas/explicaciones.py`.

**New schema change:**
- New file: `src/infraestructura/db/migrations/m{NN:02d}_{descripcion}.py` exposing `VERSION`, `DESCRIPCION`, `aplicar(conn)`.
- Append to `MIGRACIONES` in `src/infraestructura/db/migrations/__init__.py:40` (preserving declarative order).
- If it adds tables, register them in `_TABLAS_PERMITIDAS` (`src/infraestructura/db/connection.py:23`).
- Update CRUD in `src/infraestructura/db_precios.py` (and `_CAMPOS_MONETARIOS` if monetary).
- Update validation in `src/infraestructura/precios.py::_CLAVES_REQUERIDAS`.
- Tests: extend `tests/test_db_estructura.py`.

**New UI widget:**
- Reusable widget: `src/ui/inputs.py` (or new module under `src/ui/`).
- Streamlit-cached helpers: follow the pattern in `src/ui/precios_cache.py` (UI wrapper around a pure function in `src/infraestructura/`).
- Session-state keys: declare constants in `src/ui/session/claves.py` instead of inlining strings.

**New domain type:**
- Domain shape: `src/domain/tipos.py` (TypedDict) or new dataclass in `src/domain/`.
- If it is a use-case-level DTO, prefer `src/aplicacion/contratos.py`.

**Shared utilities:**
- Formatting / lookup helpers: `src/infraestructura/utils.py` (e.g. `euro`, `find_by_label`).
- Pure math constants: `src/domain/constantes.py`.

## Special Directories

**`data/`:**
- Purpose: SQLite DB + seed SQL + reference Excel JSON + static assets.
- Generated: `precios.db` is mutated at runtime; `precios.db-wal` and `precios.db-shm` are temporary WAL files (see `src/infraestructura/db/connection.py:42-44`).
- Committed: yes (the team treats the DB itself as canonical; recent commit `071849a` is "BBDD e historial").

**`notebook/`:**
- Purpose: exploratory analyses + TFG result artefacts.
- Generated: notebook output cells.
- Committed: yes.
- Not imported by `src/` or `pages/` — safe to ignore from runtime impact analysis.

**`src/infraestructura/db/migrations/`:**
- Purpose: schema evolution; idempotent.
- Generated: no — hand-written.
- Committed: yes; ordering in `__init__.py` is load-bearing (M7 before M6 by design).

**`tests/__pycache__/`, `notebook/__pycache__/`, `src/.../__pycache__/`:**
- Purpose: Python bytecode cache.
- Generated: yes.
- Committed: should not be (gitignored).

---

*Structure analysis: 2026-05-04*
