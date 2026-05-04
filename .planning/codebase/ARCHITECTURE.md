<!-- refreshed: 2026-05-04 -->
# Architecture

**Analysis Date:** 2026-05-04

## System Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                       UI (Streamlit)                             │
│   `app_licitaia.py`  (entrypoint, init_db, st.navigation)        │
├──────────────────┬──────────────────┬───────────────────────────┤
│ pages/calculadora│  pages/historial │   pages/admin_precios     │
│      .py         │       .py        │          .py              │
└────────┬─────────┴────────┬─────────┴──────────┬────────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                       src/ui/                                    │
│  inputs.py · materiales.py · precios_cache.py · theme.py         │
│  session/claves.py  (st.session_state keys)                      │
└────────┬────────────────────────────────────────────────────────┘
         │ (UI calls use cases — does not call presupuesto/dominio
         │  directly, except for ParametrosProyecto and helpers)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    src/aplicacion/  (use cases)                  │
│  calcular_presupuesto.py · editar_catalogo.py · historial.py     │
│  contratos.py  (TypedDict contracts: ResultadoPreparacion, …)    │
└────────┬───────────────────┬────────────────────┬───────────────┘
         │                   │                     │
         ▼                   ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│  src/presupuesto │  │   src/reglas     │  │  src/infraestructura │
│ bloques.py       │  │  decisor.py      │  │  precios.py          │
│ capitulos_*.py   │  │  alertas_clips.py│  │  db_precios.py       │
│ materiales.py    │  │  explicaciones.py│  │  diff_precios.py     │
│ (assembly per    │  │  normalizacion.py│  │  validacion_oficial  │
│  chapter)        │  │  templates.py    │  │  utils.py            │
│                  │  │  (CLIPS rules)   │  │  db/  (SQLite)       │
└────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘
         │                     │                        │
         ▼                     ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       src/domain/  (pure)                        │
│  parametros.py · tipos.py · constantes.py · financiero.py        │
│  geometria.py                                                    │
│  reglas/elegibilidad.py · reglas/desempates.py                   │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│             SQLite store: `data/precios.db`                      │
│   schema + 16 versioned migrations · WAL · INTEGER cents         │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Entrypoint | Init DB, configure Streamlit, declare navigation, inject theme | `app_licitaia.py` |
| Calculadora page | Form inputs, call `calcular_presupuesto`, render result, persist via `guardar_presupuesto` | `pages/calculadora.py` |
| Admin page | Edit catalogue, preview diff/drifts, call `ejecutar_guardado` | `pages/admin_precios.py` |
| Historial page | List/inspect/delete saved budgets | `pages/historial.py` |
| Use case: budget | Apply CI, re-resolve catalogue items, run decisor, assemble chapters, build financial summary | `src/aplicacion/calcular_presupuesto.py` |
| Use case: edit prices | Validate, diff, detect drift, persist | `src/aplicacion/editar_catalogo.py` |
| Use case: history | CRUD over `presupuestos*` tables | `src/aplicacion/historial.py` |
| Application contracts | TypedDicts for use case ↔ UI dialogue | `src/aplicacion/contratos.py` |
| Deterministic decisor | Eligibility + tiebreak + explanations | `src/reglas/decisor.py` |
| CLIPS expert system | Technical alerts to the licitador (only consumer of `clips`) | `src/reglas/alertas_clips.py` |
| CLIPS knowledge base | `deftemplate` / `defrule` strings + thresholds | `src/reglas/templates.py` |
| Eligibility filters | Pure Python predicates over catalogues | `src/domain/reglas/elegibilidad.py` |
| Tiebreak rules | Pure ranking functions | `src/domain/reglas/desempates.py` |
| Trench geometry | Pure math (Excel-aligned) | `src/domain/geometria.py` |
| Financial summary | PEM → GG → BI → ROUNDUP → IVA | `src/domain/financiero.py` |
| Domain types | `ItemCatalogo`, `Precios`, `ResultadoPresupuesto` | `src/domain/tipos.py` |
| Domain parameters | `ParametrosProyecto` dataclass | `src/domain/parametros.py` |
| Domain constants | `PCT_CI_DEFAULT`, `NULL_SENTINEL`, tolerances | `src/domain/constantes.py` |
| Chapter assembly | Compose chapters 01-08 from chapter functions | `src/presupuesto/bloques.py` |
| Civil-works chapters | Excavation, pipe, manholes, valves, dismantling… | `src/presupuesto/capitulos_obra_civil.py` |
| Surface chapters | Demolition, pavement, sub-base, connections | `src/presupuesto/capitulos_superficie.py` |
| Material partidas | Supply lines excluded from GG/BI base | `src/presupuesto/materiales.py` |
| Price loader | `cargar_precios` / `guardar_precios` / `aplicar_ci` | `src/infraestructura/precios.py` |
| Catalogue CRUD | Read/write tables → dict[Precios] | `src/infraestructura/db_precios.py` |
| Diff & drift | Edit-time delta and Excel cross-check | `src/infraestructura/diff_precios.py`, `validacion_oficial.py` |
| DB connection | `conectar()` ctxmgr + WAL + FK + table whitelist | `src/infraestructura/db/connection.py` |
| Schema & migrations | DDL + 16 idempotent migrations | `src/infraestructura/db/schema.py`, `db/runner.py`, `db/migrations/` |
| UI cache | Streamlit `@st.cache_data` over `cargar_precios` | `src/ui/precios_cache.py` |
| UI widgets | Re-usable input widgets (tubería, subbase, materiales) | `src/ui/inputs.py`, `src/ui/materiales.py` |
| Session keys | Constants for `st.session_state` keys | `src/ui/session/claves.py` |

## Pattern Overview

**Overall:** Layered/onion architecture with light Clean-Architecture flavour, enforced by AST-based boundary tests (`tests/test_fronteras_capas.py`). The codebase explicitly declares (in `src/aplicacion/historial.py` docstring) that it is *pragmatic*, not pure Clean: persistence is allowed inside use cases as a deliberate exception (ADR-001).

**Key Characteristics:**
- Pure domain core (`src/domain/`) — no Streamlit, no CLIPS, no SQLite imports allowed.
- Use cases (`src/aplicacion/`) orchestrate; never import Streamlit. May reach `infraestructura` directly (single-store pragmatism).
- Two-pillar expert reasoning: deterministic decisor (Python) for material selection + CLIPS engine for alerts only. Memory of the project (TFG) makes this distinction structural.
- Single CLIPS importer: only `src/reglas/alertas_clips.py` may `import clips` (verified by `test_solo_alertas_clips_importa_clips`).
- Persistence is SQLite with a closed table whitelist (`_TABLAS_PERMITIDAS`) and INTEGER-cents storage (Migration M13).
- UI surface is Streamlit only and isolated under `pages/` and `src/ui/`.

## Layers

**`src/domain/` — Domain core:**
- Purpose: invariants, types, parameters, pure formulas (geometry, finance), pure rule predicates.
- Location: `src/domain/`
- Contains: dataclasses, TypedDicts, frozen constants, pure Python functions.
- Depends on: stdlib only (`math`, `dataclasses`, `typing`, `logging`).
- Used by: every other layer.
- Forbidden imports: `streamlit`, `clips`, `sqlite3` (enforced).

**`src/presupuesto/` — Budget assembly:**
- Purpose: turn parameters + resolved items + decisions into `(subtotal, partidas)` per chapter.
- Location: `src/presupuesto/`
- Contains: `bloques.py` (orchestrates), `capitulos_obra_civil.py`, `capitulos_superficie.py`, `materiales.py`.
- Depends on: `src/domain/` (geometry, types).
- Used by: `src/aplicacion/calcular_presupuesto.py`.
- Forbidden imports: `streamlit`, `clips`, `sqlite3`.

**`src/reglas/` — Reasoning layer:**
- Purpose: deterministic decisor + CLIPS-based alerts + explanations.
- Location: `src/reglas/`
- Contains: `decisor.py` (pure orchestrator), `alertas_clips.py` (CLIPS adapter, only `clips` importer), `explicaciones.py` (string formatting), `normalizacion.py`, `templates.py` (CLIPS DSL strings + thresholds).
- Depends on: `src/domain/` (constants, tipos, eligibility, desempates).
- Used by: `src/aplicacion/calcular_presupuesto.py`, `pages/calculadora.py` (alerts only).
- Forbidden imports per file declared in `tests/test_fronteras_capas.py::_REGLAS_REGLAS`.

**`src/aplicacion/` — Use cases:**
- Purpose: orchestrate domain + infrastructure for each user flow.
- Location: `src/aplicacion/`
- Contains: `calcular_presupuesto.py`, `editar_catalogo.py`, `historial.py`, `contratos.py`.
- Depends on: `src/domain/`, `src/presupuesto/`, `src/reglas/`, `src/infraestructura/`.
- Used by: `pages/*.py`.
- Forbidden imports: `streamlit` (must stay UI-agnostic).

**`src/infraestructura/` — Adapters:**
- Purpose: SQLite access, Excel cross-validation, formatting helpers.
- Location: `src/infraestructura/`
- Contains: `precios.py`, `db_precios.py`, `diff_precios.py`, `validacion_oficial.py`, `utils.py`, sub-package `db/` with `connection.py`, `schema.py`, `runner.py`, `helpers.py`, `migrations/m01..m16`.
- Depends on: `src/domain/` (constants).
- Used by: `src/aplicacion/`, `src/ui/precios_cache.py`.
- Forbidden imports: `streamlit`.

**`src/ui/` — Streamlit surface:**
- Purpose: cached price loader, widgets, theming, session-state key constants.
- Location: `src/ui/`
- Contains: `precios_cache.py`, `inputs.py`, `materiales.py`, `theme.py`, `session/claves.py`.
- Depends on: `src/infraestructura/`, `src/presupuesto/` (only for `materiales_demo_disponibles`).
- Used by: `pages/*.py`, `app_licitaia.py`.

**`pages/` — Streamlit pages:**
- Purpose: page-level routing, form composition, render result.
- Used by: `app_licitaia.py` via `st.navigation`.

## Data Flow

### Primary Request Path — Compute a budget

1. User submits form on `pages/calculadora.py:73+`.
2. Page calls `cargar_precios()` (`src/ui/precios_cache.py:23`) — Streamlit-cached for 60 s.
3. Page builds a `ParametrosProyecto` (`src/domain/parametros.py:14`).
4. Page calls `calcular_presupuesto(p, precios, overrides)` (`src/aplicacion/calcular_presupuesto.py:153`).
5. Use case `deepcopy`s `precios` and applies CI via `aplicar_ci` (`src/infraestructura/precios.py`).
6. `_reresolver_items_ci` re-resolves user-selected catalogue items with CI (`calcular_presupuesto.py:62`). Fail-fast on miss.
7. Per active red, calls `resolver_decisiones(...)` (`src/reglas/decisor.py:66`):
   - `elegibles_*` (`src/domain/reglas/elegibilidad.py`).
   - `desempatar_*` / `ordenar_valvuleria` (`src/domain/reglas/desempates.py`).
   - `generar_explicaciones(...)` (`src/reglas/explicaciones.py`).
8. Optional user `overrides` are applied via `_aplicar_overrides` (`calcular_presupuesto.py:103`).
9. Chapters 01–08 are assembled by the `ensamblar_*` functions in `src/presupuesto/bloques.py` (lines 61–399), which delegate to `capitulo_*` in `capitulos_obra_civil.py` / `capitulos_superficie.py` and accumulate via `_acumular`.
10. `calcular_resumen(...)` (`src/domain/financiero.py:36`) computes GG / BI / PBL / IVA / TOTAL — Excel-aligned ROUNDUP-to-decade.
11. Result returned as `ResultadoPresupuesto` dict (`src/domain/tipos.py:147`) and stored in `st.session_state[sk.RESULTADO]`.
12. On "Guardar en historial", page calls `guardar_presupuesto(...)` (`src/aplicacion/historial.py:29`) which inserts into `presupuestos`, `presupuesto_capitulos`, `presupuesto_partidas`, `presupuesto_parametros`, `presupuesto_trazabilidad`.

### CLIPS alert flow

1. After result computation, page calls `generar_alertas_tecnicas(...)` (`src/reglas/alertas_clips.py:58`).
2. A fresh `clips.Environment()` is created per call.
3. Templates and rules from `src/reglas/templates.py` are built into the environment (`_iter_construcciones`).
4. A single `(datos-proyecto …)` fact is asserted with the project parameters.
5. Inference runs; produced `etiqueta` and `alerta` facts are collected and returned as a dict for the UI badge/banner.

### Edit-prices flow

1. `pages/admin_precios.py:24` calls `cargar_todo()` (`src/infraestructura/db_precios.py`) — uncached for fresh values.
2. User edits dataframes; on submit, page calls `preparar_guardado(editados, originales)` (`src/aplicacion/editar_catalogo.py:33`).
3. `_validar_precios` → `calcular_diff` → `detectar_drifts` populate `ResultadoPreparacion`.
4. If `puede_guardar`, page calls `ejecutar_guardado(editados)` → `guardar_precios(...)` (`src/infraestructura/precios.py`).
5. Page calls `cargar_precios.clear()` to invalidate the Streamlit cache.

**State Management:**
- Streamlit `st.session_state` keyed by constants in `src/ui/session/claves.py` (e.g. `RESULTADO`, `INSTALACION_VALVULERIA`, `PRECIOS_ORIGINALES`, `CONFIRMAR_GUARDADO`).
- Price snapshot for diffing is stored in `session_state[sk.PRECIOS_ORIGINALES]` as a `deepcopy`.
- No global mutable state outside `st.session_state` and the module-level `_GLOBAL_CSS` string.

## Key Abstractions

**`ParametrosProyecto` (dataclass):**
- Purpose: complete user input for one budget computation.
- File: `src/domain/parametros.py:14`.
- Pattern: dataclass with derived `@property`s (`aba_activa`, `aba_diametro_mm`, `aba_tipo`).

**`Precios` (TypedDict, total=False):**
- Purpose: shape of the catalogue dict returned by `cargar_precios()`.
- File: `src/domain/tipos.py:85`.
- Pattern: `total=False` because some catalogues may be empty.

**`ItemCatalogo` (TypedDict, total=False):**
- Purpose: unified shape for any catalogue row (pipe, manhole, valve, demolition, …).
- File: `src/domain/tipos.py:23`.

**`ResumenFinanciero` (frozen dataclass):**
- Purpose: immutable financial summary.
- File: `src/domain/financiero.py:25`.

**`GeometriaZanja` (frozen dataclass):**
- Purpose: immutable trench geometry result.
- File: `src/domain/geometria.py:25`.

**`ResultadoPreparacion` (TypedDict):**
- Purpose: contract returned by `preparar_guardado` for the admin UI.
- File: `src/aplicacion/contratos.py:49`.

**`NULL_SENTINEL = "*"`:**
- Purpose: wildcard marker for catalogue / CLIPS facts.
- File: `src/domain/constantes.py:38`.

## Entry Points

**`app_licitaia.py`:**
- Location: `app_licitaia.py`
- Triggers: `streamlit run app_licitaia.py` (Dockerfile `CMD`).
- Responsibilities: configure `logging.basicConfig(level=DEBUG)`, call `init_db()`, set page config, inject CSS, declare `st.navigation([...])`.

**`init_db()`:**
- Location: `src/infraestructura/db/runner.py:30`
- Triggers: called once from `app_licitaia.py:32`.
- Responsibilities: run DDL `_SCHEMA`, ensure `schema_version` table, dispatch pending migrations from `MIGRACIONES`.

**`pages/calculadora.py`, `pages/historial.py`, `pages/admin_precios.py`:**
- Triggers: Streamlit `st.navigation` switching.
- Responsibilities: page-scoped UI; rerun-driven control flow.

## Architectural Constraints

- **Threading:** single-threaded Streamlit script reruns. `journal_mode = WAL` is enabled in `src/infraestructura/db/connection.py:49` so multiple browser tabs/reruns can read while one writes without `database is locked`.
- **Global state:** no module-level mutable singletons. Streamlit `@st.cache_data(ttl=60)` decorates `cargar_precios` in `src/ui/precios_cache.py:22`. The CLIPS environment is created *fresh per call* in `alertas_clips.generar_alertas_tecnicas` (no shared engine).
- **Money representation:** SQLite stores monetary fields as `INTEGER` cents since Migration M13 (`src/infraestructura/db_precios.py:7`). Conversion to float € happens at the loader boundary; the rest of the system works in `float`.
- **CI invariant:** `BD.precio × pct_ci ≈ precio_oficial_Excel`. Tolerance: `TOLERANCIA_INVARIANTE_CI = 0.005` (`src/domain/constantes.py:29`). Enforced by `tests/test_bd_invariante_ci.py` and used by migrations.
- **Layer fences (AST-tested):** see `tests/test_fronteras_capas.py::_REGLAS` and `_REGLAS_REGLAS`.
  - `src/domain/**` may not import `streamlit`, `clips`, `sqlite3`.
  - `src/aplicacion/**` may not import `streamlit`.
  - `src/presupuesto/**` may not import `streamlit`, `clips`, `sqlite3`.
  - `src/infraestructura/**` may not import `streamlit`.
  - In `src/reglas/`, only `alertas_clips.py` may import `clips` (single documented exception in `_EXCEPCIONES`).
- **Migration ordering:** `MIGRACIONES` list in `src/infraestructura/db/migrations/__init__.py:40` is **declarative, not numeric** — M7 deliberately runs before M6 to preserve original behaviour. Do not re-sort.
- **Closed table whitelist:** `_TABLAS_PERMITIDAS` (`src/infraestructura/db/connection.py:23`) gates dynamic SQL in `_cargar_por_red`.

## Anti-Patterns

### Importing CLIPS outside `src/reglas/alertas_clips.py`

**What happens:** A new module under `src/reglas/` or elsewhere does `import clips`.
**Why it's wrong:** It blurs the TFG narrative ("CLIPS only emits alerts; selection is deterministic") and breaks `tests/test_fronteras_capas.py::test_solo_alertas_clips_importa_clips`.
**Do this instead:** keep CLIPS use inside `src/reglas/alertas_clips.py:1` only. For deterministic logic, extend `src/reglas/decisor.py` and `src/domain/reglas/`.

### Streamlit import inside use cases or domain

**What happens:** A function under `src/aplicacion/`, `src/domain/`, `src/presupuesto/` or `src/infraestructura/` `import streamlit as st`.
**Why it's wrong:** Couples the layer to the UI runtime, prevents CLI/notebook reuse, breaks the AST tests.
**Do this instead:** keep Streamlit calls in `pages/` and `src/ui/`. If caching is needed, mirror the pattern in `src/ui/precios_cache.py:22` (a thin Streamlit wrapper around a pure function).

### Mutating the loaded `precios` dict in place

**What happens:** Code that receives `precios` from `cargar_precios()` mutates a catalogue inline (e.g. multiplying prices by `pct_ci`).
**Why it's wrong:** The caller's reference is shared across reruns via the Streamlit cache; mutation poisons subsequent loads. The CI invariant becomes unverifiable.
**Do this instead:** `copy.deepcopy(precios_base)` before any transformation, exactly as `src/aplicacion/calcular_presupuesto.py:191` does.

### Editing `_SCHEMA` for new schema changes

**What happens:** A new column / table is added by editing `src/infraestructura/db/schema.py`.
**Why it's wrong:** Existing databases never re-run `_SCHEMA`; only `init_db()` will create *missing* tables. A column added there is invisible to deployed BDs.
**Do this instead:** add a new file `src/infraestructura/db/migrations/m17_*.py` with `VERSION`, `DESCRIPCION`, `aplicar(conn)`, append it to `MIGRACIONES` in `src/infraestructura/db/migrations/__init__.py:40`.

### Returning silent zeros / empties on missing items

**What happens:** A helper returns `0.0` or `[]` when a catalogue item or price is missing.
**Why it's wrong:** Hides data corruption; the budget undercounts silently. The codebase already settled on fail-fast — see `_importe` (`src/presupuesto/capitulos_obra_civil.py:28`) and `_reresolver_items_ci` (`src/aplicacion/calcular_presupuesto.py:73`).
**Do this instead:** raise `ValueError` with an actionable message in Spanish.

### Hardcoding `1.05` (CI factor) inline

**What happens:** A literal `* 1.05` or `pct_ci = 1.05` appears outside `src/domain/constantes.py`.
**Why it's wrong:** Breaks the single-source-of-truth declared in the docstring of `src/domain/constantes.py:17`.
**Do this instead:** import `PCT_CI_DEFAULT` from `src.domain.constantes`.

## Error Handling

**Strategy:** fail-fast at boundaries, friendly messages in UI.

**Patterns:**
- Loaders raise `ValueError` with a Spanish message; pages catch them and render `st.error(...)` followed by `st.stop()` — see `pages/calculadora.py:32-40` and `pages/admin_precios.py:26-32`.
- Calculation primitives raise `ValueError` on `None`, negative, or non-finite values (`src/presupuesto/capitulos_obra_civil.py:28`).
- Use cases (`historial.guardar_presupuesto`) wrap DB writes in `try/except`, `conn.rollback()`, `logger.error(..., exc_info=True)`, then re-raise.
- The CI re-resolution step is fail-fast: a missing label aborts the whole budget rather than producing a 5 % undervaluation (`calcular_presupuesto.py:73-79`).

## Cross-Cutting Concerns

**Logging:** standard `logging` with `basicConfig(level=DEBUG)` at `app_licitaia.py:21`. Every module does `logger = logging.getLogger(__name__)`. The format includes file:func:line. DEBUG is intentionally noisy (decision traceability for the TFG); production would lower to INFO.

**Validation:** redundant on purpose — Python validation in `src/infraestructura/precios.py:_validar_precios` produces friendly Spanish errors; SQLite `CHECK` and `FOREIGN KEY` constraints (Migration M12) are the silent safety net.

**Authentication:** none. The app is single-user / local. No auth layer in `pages/` or anywhere else.

**Persistence:** single-store SQLite at `data/precios.db`. WAL + foreign_keys ON. Connections are short-lived `with conectar() as conn:` blocks. No ORM.

**Caching:** Streamlit `@st.cache_data(ttl=60)` on `cargar_precios` only; everything else re-computes per rerun. Manual `cargar_precios.clear()` after admin saves.

---

*Architecture analysis: 2026-05-04*
