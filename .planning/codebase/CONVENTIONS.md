# Coding Conventions

**Analysis Date:** 2026-05-04

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g. `calcular_presupuesto.py`, `db_precios.py`, `alertas_clips.py`).
- Test files: `test_<unidad>.py` directly under `tests/` (e.g. `tests/test_calculadora.py`, `tests/test_audit.py`).
- Migrations: `m<NN>_<slug>.py` with two-digit zero-padded version (e.g. `src/infraestructura/db/migrations/m12_check_constraints.py`).
- Streamlit pages: `pages/<nombre>.py` (Streamlit auto-discovers pages by filename).

**Functions:**
- Public API functions in `snake_case`, action-first verb in Spanish, e.g. `calcular_presupuesto`, `cargar_precios`, `generar_alertas_tecnicas`, `resolver_decisiones` (`src/aplicacion/calcular_presupuesto.py`, `src/infraestructura/precios.py`, `src/reglas/alertas_clips.py`).
- Internal helpers prefixed with `_` (e.g. `_resolver_item_ci`, `_aplicar_overrides`, `_acumular`, `_iter_construcciones`).
- Test helpers in `tests/helpers.py` are also `_`-prefixed (`_app_calculadora`, `_calcular_aba`, `_calcular_san`, `_resultado_minimal`).

**Variables:**
- `snake_case` everywhere. Spanish domain terms preserved (`pem`, `pbl_sin_iva`, `pct_gg`, `pct_bi`, `pct_iva`, `pct_ci`, `pct_seguridad`, `aba_longitud_m`, `san_profundidad_m`).
- Magnitudes carry their unit suffix: `_m` (metros), `_m2`, `_m3`, `_mm`, `_pm` ("por metro lineal"), `_pct` (fracción 0-1).
- Booleans use `es_*` / `aba_activa` / `hay_*` (e.g. `es_san`, `hay_entibacion`, `p.aba_activa`).

**Types / Classes:**
- Dataclasses and `TypedDict` use `PascalCase`: `ParametrosProyecto`, `ResumenFinanciero`, `GeometriaZanja`, `ItemCatalogo`, `Precios`, `ResultadoPresupuesto`, `CapituloResultado`, `ResultadoPreparacion` (`src/domain/parametros.py`, `src/domain/financiero.py`, `src/domain/geometria.py`, `src/domain/tipos.py`, `src/aplicacion/contratos.py`).
- Frozen dataclasses for value objects: `@dataclass(frozen=True) class GeometriaZanja`, `@dataclass(frozen=True) class ResumenFinanciero`.

**Constants:**
- Module-level `UPPER_SNAKE_CASE` (e.g. `PCT_CI_DEFAULT`, `TOLERANCIA_INVARIANTE_CI`, `NULL_SENTINEL`, `UMBRALES`, `FACTORES_PIEZAS`, `_TABLAS_PERMITIDAS`, `_CLAVES_REQUERIDAS`).
- Domain-wide canonical constants live in `src/domain/constantes.py` and MUST be imported, never duplicated as literals (enforced by `tests/test_constantes_dominio.py::test_precios_py_no_tiene_1_05_literal_en_codigo_vivo`).

## Code Style

**Formatting:**
- No formatter (no `.prettierrc`, no `pyproject.toml`, no Black/Ruff config) — formatting is manual but consistent: 4-space indent, ~100 column lines, blank lines around section banners.
- ASCII section banners using `# ─── ... ────────────` or `# ═══ ... ═══` are common in long modules to separate areas (`src/aplicacion/calcular_presupuesto.py`, `pages/calculadora.py`).

**Linting:**
- No linter is configured. The project has no ESLint/Ruff/mypy config files at the root.
- Static-type intent declared via `from __future__ import annotations` in EVERY `.py` file (src and tests) and `TypedDict` shapes in `src/domain/tipos.py` for documentation, but no CI enforcement.

**Encoding / shebang:**
- No shebangs. UTF-8 implicit. Spanish accents are preserved in code (variable names, strings, banners).
- Files explicitly use `read_text(encoding="utf-8")` when loading sources for AST analysis (`tests/test_fronteras_capas.py`, `tests/test_constantes_dominio.py`).

## Import Organization

**Order (observed):**
1. `from __future__ import annotations` — first non-comment line in every module.
2. Stdlib imports (`import logging`, `import os`, `import math`, `import sqlite3`, `from pathlib import Path`).
3. Third-party imports (`import streamlit as st`, `import pandas as pd`, `import clips`, `import pytest`).
4. Project imports (`from src.domain...`, `from src.aplicacion...`, `from src.infraestructura...`).

Example: `app_licitaia.py`, `pages/calculadora.py`, `src/aplicacion/calcular_presupuesto.py`.

**Path aliases:**
- None. The repo root is added to `sys.path` indirectly via `tests/conftest.py:os.chdir(_project_root)` and `sys.path.insert(0, ...)`. Production imports use the absolute `src.` prefix.

**Layered import discipline (enforced):**
- `src/domain/**` MUST NOT import `streamlit`, `clips`, or `sqlite3` (`tests/test_fronteras_capas.py::_REGLAS`).
- `src/aplicacion/**` MUST NOT import `streamlit`.
- `src/presupuesto/**` MUST NOT import `streamlit`, `clips`, or `sqlite3`.
- `src/infraestructura/**` MUST NOT import `streamlit` (the cache wrapper lives in `src/ui/precios_cache.py`).
- Only `src/reglas/alertas_clips.py` may import `clips` (verified by `tests/test_fronteras_capas.py::test_solo_alertas_clips_importa_clips` and `tests/test_reglas_estructura.py`).
- Exceptions to layer rules MUST be added to `_EXCEPCIONES` in `tests/test_fronteras_capas.py` with a written justification comment.

## Error Handling

**Strategy:**
- **Fail-fast on inconsistency.** When invariants would otherwise produce silent infraestimation, raise `ValueError` with a Spanish, actionable message that names the offending entity.
  - `src/aplicacion/calcular_presupuesto.py:_reresolver_items_ci` raises if a label disappears after applying CI ("Item '{label}' del catálogo '{catalogo_key}' no se resolvió tras aplicar el CI...").
  - `src/presupuesto/bloques.py:ensamblar_acometidas` raises if the default acometida type is missing in the catálogo ("Actualízalo en Administración de precios.").
  - `src/infraestructura/utils.py:find_item` / `find_by_label` raise with the list of available labels when nothing matches.
- **No silent defaults for domain values.** `pct_ci` defaults to `1.0` (neutral) if the dict key is missing, but `1.05` is the canonical EMASESA factor and must come from `PCT_CI_DEFAULT` in `src/domain/constantes.py` — never as a literal in code (see `tests/test_constantes_dominio.py`).
- **UI surfaces errors via `st.error` + `st.stop`** when bootstrap is impossible (`pages/calculadora.py` lines 32-64: failed `cargar_precios()` or empty catálogos halt the page with a Spanish message pointing the user to "Administración de precios").
- **Validation lists, not exceptions, for user input.** `src/infraestructura/utils.py:validar_parametros` returns `list[str]` of error strings; `src/infraestructura/precios.py:_validar_precios` returns errors before raising. Two-layer validation: Python for legible messages + SQLite FK/CHECK constraints as silent backstop (`src/infraestructura/db/migrations/m12_check_constraints.py`).

**Patterns:**
- Always include the offending value in the error string (label, dn, longitud, available options).
- When silently defaulting is the right call, log a `WARNING` with the affected entity (`src/reglas/normalizacion.py:factor_piezas` returns 1.0 + WARNING; `src/aplicacion/calcular_presupuesto.py:_resolver_item_ci` warns when CI resolution fails).

## Logging

**Framework:** stdlib `logging`. Configured once at the entrypoint (`app_licitaia.py` lines 21-27) at `DEBUG` level with the format `"%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"`. Comment in entrypoint instructs production to switch to `logging.INFO`.

**Pattern:**
```python
import logging
logger = logging.getLogger(__name__)   # one per module, top-level after imports
```

**Levels and use cases:**
- `INFO` for milestones (start/end of `calcular_presupuesto`, per-capítulo subtotal, financial summary line).
- `DEBUG` for intermediate values (geometry breakdowns, item resolution, per-partida acumulación).
- `WARNING` when silently degrading (CI item not found, factor_piezas fallback, empty catalog).
- `ERROR` only when a `raise` is imminent or an `find_item`/`find_by_label` lookup failed.

**Tag prefixes** (informal, but consistent across the codebase):
- `[CI-RESOLVE]` — re-resolution after applying CI.
- `[GEO-ABA]` / `[GEO-SAN]` — per-network geometry trace.
- `[FIN]` — financial summary (`src/domain/financiero.py`).
- `[ABA]`, `[SAN]`, `[PAV-ABA]`, `[PAV-SAN]`, `[ACOM-ABA]`, `[ACOM-SAN]` — capítulo-scoped logs in `src/presupuesto/bloques.py`.
- `[ELEG]` — elegibilidad in `src/reglas/decisor.py`.
- `[SE]` — sistema experto in `src/reglas/alertas_clips.py`.
- `[ACUM]`, `[FACTOR-PIEZAS]` — generic helpers.

**Box-drawing markers** (visual milestone separators in INFO logs):
- `═══ calcular_presupuesto INICIO ═══` / `═══ calcular_presupuesto FIN - TOTAL %.2f € ═══`
- `── CAP 01: OBRA CIVIL ABA ──`, `── RESUMEN FINANCIERO ──`

Logs are intentionally verbose; they are the project's diagnosis tool (per the testing-strategy convention "logging para diagnóstico").

## Comments

**When to comment:**
- Every public function and module has a triple-quoted Spanish docstring explaining purpose, the Excel/EMASESA cell or rule it derives from, and the contract (Args/Returns).
- Inline comments are reserved for non-obvious branches: cite the Excel cell (`# Excel H69`, `# F62`), the migration (`# Audit A2C 2026-04-19`), or the convention being upheld (`# Convención EMASESA: ABA SUM(J57:J60) excluye e)Materiales...`).
- Architectural rationale (why a layer cannot import X, why a literal is forbidden, why a fallback is neutral) lives directly in the module docstring (see `src/domain/constantes.py`, `src/infraestructura/precios.py`, `src/reglas/alertas_clips.py`).

**No emojis.** Strict project convention: no emojis in UI strings, log messages, docstrings, comments, or test assertions. Differentiate severity via color/typography in CSS (`src/ui/theme.py`) and via text prefixes (`[CRÍTICO]`, `(error)`, `(warning)`) in messages — never via emoji.

**JSDoc/TSDoc:** N/A (Python project). Docstrings follow informal Google-ish style: opening summary, blank line, optional Args/Returns blocks. Type hints carry the formal contract; docstrings explain the *why*.

**Reference comments to source authority:** when a number, formula, or rule is anchored to an external source, the comment names that source verbatim — e.g. `# Excel EMASESA`, `# RD 396/2006`, `# audit BD-Excel A2C 2026-04-19`, `# NTE-ADZ`. This anchors the code to the TFG memoria.

## Function Design

**Size:** Most pure-domain functions are 5-30 lines (`src/domain/geometria.py`, `src/domain/financiero.py`). Orchestrators (`calcular_presupuesto`, ensamblar_*) reach 50-150 lines but are flat compositions of helpers, not deep nesting.

**Parameters:**
- Keyword-only arguments via `*,` after positionals when there are >3 args (e.g. helpers in `tests/helpers.py: _calcular_aba(at, *, dn, longitud, profundidad)`).
- Default values are domain-meaningful (e.g. `pct_manual: float = 0.30`, `aba_profundidad_m: float = 1.20` in `ParametrosProyecto`).
- Pass mutable shared state explicitly as a `caps: dict` + `estado: dict` pair to ensamblers — never as a global.

**Return values:**
- Pure-calculation functions return frozen dataclasses (`GeometriaZanja`, `ResumenFinanciero`) so callers cannot mutate.
- Use cases return `TypedDict` (`ResultadoPresupuesto`, `ResultadoPreparacion`) so the contract is documented but stays JSON-serialisable for SQLite persistence.
- Validation functions return `list[str]` (empty == OK) instead of raising.
- Tuples `(subtotal, partidas)` returned by `capitulo_*` builders, accumulated by `_acumular`.

## Module Design

**Exports:**
- Public API surfaces are documented in the module docstring under "API pública" (`src/reglas/alertas_clips.py`, `src/reglas/decisor.py`, `src/aplicacion/calcular_presupuesto.py`).
- No `__all__` declared; imports work directly via `from src.X.Y import Z`.

**Barrel files:**
- `src/aplicacion/__init__.py` exports the three use cases (lightweight re-export only).
- `src/infraestructura/db/__init__.py` re-exports the legacy monolith API (`conectar`, `init_db`, `DB_PATH`, `_TABLAS_PERMITIDAS`) — verified by `tests/test_db_estructura.py::test_api_publica_preservada`.
- Other packages do NOT use barrels; direct module paths are preferred.

## Architectural Conventions Specific to LicitaIA

**Sistema experto vs decisor:**
- CLIPS (`src/reglas/alertas_clips.py` + `src/reglas/templates.py`) ONLY emits **alertas técnicas** to the licitador. It does NOT select materials.
- Material selection is **deterministic Python** (`src/reglas/decisor.py` calling `src/domain/reglas/elegibilidad.py` and `src/domain/reglas/desempates.py`).
- Every new module under `src/reglas/` MUST be checked against `tests/test_reglas_estructura.py` to ensure it does not import `clips` unless its purpose is the inferencia engine.

**Alertas language convention** (sistema experto output):
- The `msg` field of every CLIPS `(alerta ...)` MUST be:
  - **Short** (one sentence, conversational).
  - **Plain Spanish** (no jargon, no acronyms unless universal).
  - **No normative citations in the body** — those go in the `fuente` slot (e.g. `fuente "RD 396/2006"`, `fuente "Excel EMASESA"`, `fuente "regla interna"`).
- Examples (from `src/reglas/templates.py`):
  - `"Hay fibrocemento pero la Gestion Ambiental esta al 0%. Revisa ese porcentaje."` + `fuente "RD 396/2006"`.
  - `"Red ABA larga sin acometidas. Has comprobado si existen?"` + `fuente "regla interna"`.
- Two independent dimensions: `severidad` (alta|media|baja) belongs to `etiqueta` facts, `nivel` (error|warning|info) belongs to `alerta` facts. Never confuse them.

**CI invariant** (`PCT_CI_DEFAULT = 1.05`):
- BD stores precios **base sin CI**. Runtime applies CI on a `deepcopy` (`src/infraestructura/precios.py:aplicar_ci`, `src/aplicacion/calcular_presupuesto.py` lines 191-194). Never mutate the caller's dict.
- The factor `1.05` is forbidden as a literal in production code — must be imported from `src.domain.constantes.PCT_CI_DEFAULT` (enforced by `tests/test_constantes_dominio.py`).

**Catalog evolution rule:**
- To close a gap LicitaIA-vs-Excel/BC3, the FIRST hypothesis is "missing catalog variant", not "missing multiplier". Add new rows to catálogos (FD, acometidas, pavimentos…). Existing rows that already match the EMASESA Excel are NOT touched.

**Locale and units:**
- All user-facing strings in Spanish.
- Currency formatting: `src/infraestructura/utils.py:euro` outputs `1.234,56 €` (Spanish locale: dot for thousands, comma for decimals).
- All physical magnitudes in SI base units inside the domain (m, m², m³, kg). Conversion happens at UI/Excel boundaries only.

---

*Convention analysis: 2026-05-04*
