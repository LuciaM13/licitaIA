# Testing Patterns

**Analysis Date:** 2026-05-04

## Test Framework

**Runner:**
- `pytest` >=8.0,<9.0 (`requirements-dev.txt`).
- Configuration: minimal — there is no `pytest.ini`, `pyproject.toml`, or `setup.cfg`. All setup happens in `tests/conftest.py`.
- Test discovery: pytest's default (`tests/test_*.py`).

**Streamlit testing:**
- `streamlit.testing.v1.AppTest` — primary harness for end-to-end behaviour of the Streamlit pages (`tests/helpers.py`, `tests/test_calculadora.py`, `tests/test_admin.py`, `tests/test_historial.py`).
- `default_timeout=10` is passed when AppTest needs more than the library default (`tests/test_admin.py`).

**Assertion library:**
- Plain `assert` + `pytest.approx` for float comparisons. No `unittest`, no Hamcrest.
- Tolerance convention: `abs=0.01` for currency (cents), `abs=1e-4` for dimensions in metres, `abs=0.001` for percentage fractions, `abs=1e-5` for small volumes (`tests/test_audit.py`, `tests/test_validacion_excel.py`).

**Run commands:**
```bash
conda activate licitaia
pytest tests/ -v                              # Full suite
pytest tests/test_calculadora.py -v           # Single file
pytest tests/test_snapshot_excel.py -v        # Baseline contra Excel
pytest tests/test_etiquetas.py -v             # Sistema experto CLIPS
```

The conda environment `licitaia` is the canonical execution context (named in module docstrings of `tests/test_audit.py`, `tests/test_snapshot_excel.py`).

## Test File Organization

**Location:**
- All tests in a single flat `tests/` directory (`C:\Users\isma_\Desktop\licitaIA\tests\`). NOT co-located with source.

**Naming:**
- `test_<area>.py` where `<area>` reflects the layer or behaviour, NOT the module under test 1:1. Examples:
  - `tests/test_calculadora.py` — AppTest for `pages/calculadora.py`.
  - `tests/test_admin.py` — AppTest for `pages/admin_precios.py`.
  - `tests/test_historial.py` — AppTest for `pages/historial.py`.
  - `tests/test_audit.py` — pure-function audits of `src/domain/geometria.py` + `src/domain/financiero.py`.
  - `tests/test_snapshot_excel.py` — baseline anchored to Excel EMASESA.
  - `tests/test_validacion_excel.py` — formula validation against Excel cells.
  - `tests/test_etiquetas.py` — CLIPS sistema experto inference.
  - `tests/test_bd_invariante_ci.py` — invariant `BD × pct_ci ≈ Excel`.
  - `tests/test_fronteras_capas.py` / `test_reglas_estructura.py` / `test_aplicacion_estructura.py` / `test_db_estructura.py` / `test_infraestructura_pura.py` — AST-based architectural invariants.
  - `tests/test_constantes_dominio.py` — anchor canonical constants and forbid literal duplication.
  - `tests/test_tipos_domain.py` / `test_etiquetas.py` / `test_fail_fast_precios.py` / `test_historial_snapshot.py` — narrow contract tests.

**Structure:**
```
tests/
├── __init__.py            # Empty marker
├── conftest.py            # Bootstraps cwd + sys.path + init_db()
├── helpers.py             # AppTest factories shared across files
├── test_admin.py
├── test_aplicacion_estructura.py
├── test_audit.py
├── test_bd_invariante_ci.py
├── test_calculadora.py
├── test_constantes_dominio.py
├── test_db_estructura.py
├── test_etiquetas.py
├── test_fail_fast_precios.py
├── test_fronteras_capas.py
├── test_historial.py
├── test_historial_snapshot.py
├── test_infraestructura_pura.py
├── test_reglas_estructura.py
├── test_snapshot_excel.py
├── test_tipos_domain.py
└── test_validacion_excel.py
```

## Bootstrap and Shared Setup

**`tests/conftest.py` does three things at import time:**
1. `os.chdir(_project_root)` — fixes cwd so `pages/calculadora.py` resolves relative paths the same way Streamlit does.
2. `sys.path.insert(0, os.path.dirname(__file__))` — makes `from helpers import ...` work in test files.
3. `init_db()` — applies the full migration chain (16 migrations) before any test runs.

There is NO `tests/conftest.py` fixture surface. All bootstrapping is module-level side-effect.

## Test Structure

**Suite organization:**
Test files use heavy banner separators and group related assertions:

```python
# ═══════════════════════════════════════════════════════════════════════════════
# Ronda 1 - Tests básicos
# ═══════════════════════════════════════════════════════════════════════════════

def test_calculadora_carga():
    """La pagina de calculadora carga sin excepciones."""
    at = _app_calculadora().run()
    assert not at.exception
```

Each test:
- Has a Spanish, one-line docstring describing the scenario.
- Imports helpers from `tests/helpers.py` to avoid duplicating Streamlit widget wiring.
- Asserts behaviour via `at.session_state` after `at.run()` rather than parsing UI elements when possible.

**Patterns:**
- Setup: build a fresh `AppTest` per test (`_app_calculadora().run()`) — no shared state between tests.
- Teardown: not needed for AppTest (each instance is throwaway). For tests that mutate the DB (`tests/test_admin.py::test_admin_guardar_valido`), wrap in `try/finally` to restore the original value.
- Assertion shape: `assert not at.exception` first, then drill into `at.session_state["resultado"]`.

## Testing Strategy (Project Convention)

**Solo AppTest, nunca pytest unitarios.** This is the canonical convention for behaviour tests of UI flows: never write a pytest function that imports from `pages/calculadora.py` directly or that mocks Streamlit widgets. Always go through `streamlit.testing.v1.AppTest`.

**Justified exceptions** to the "solo AppTest" rule (each test file declares the exception in its module docstring):

| File | Reason for the exception |
|------|--------------------------|
| `tests/test_audit.py` | Pure-function audit of `src/domain/geometria.py` and `src/domain/financiero.py` — no Streamlit surface to drive. |
| `tests/test_validacion_excel.py` | Formula validation against Excel cells — no UI. |
| `tests/test_snapshot_excel.py` | Baseline of `calcular_presupuesto()` against Excel EMASESA — pure-function call. |
| `tests/test_etiquetas.py` | CLIPS engine has no Streamlit surface; chained inference is the TFG defence argument and merits direct testing. |
| `tests/test_fronteras_capas.py` | AST-based architectural invariant; "estructural puro sin superficie Streamlit". |
| `tests/test_reglas_estructura.py` | Same — verifies layout of `src/reglas/`. |
| `tests/test_aplicacion_estructura.py` | Contract tests for `src/aplicacion/`. |
| `tests/test_db_estructura.py` | Verifies migrations and `init_db()` schema_version. |
| `tests/test_infraestructura_pura.py` | Verifies `src/infraestructura/precios.py` does not import Streamlit (subprocess test). |
| `tests/test_bd_invariante_ci.py` | SELECT-puro on `data/precios.db` — no Streamlit. |
| `tests/test_constantes_dominio.py` | AST check that `1.05` is not a literal in production code. |

If you add a new pytest test that does not use AppTest, you MUST add a module docstring section declaring the exception and the reason — typically referencing AGENTS.md.

**Logging para diagnóstico:** When a test fails or you need to understand why an AppTest produced an unexpected `at.session_state`, the project's diagnosis tool is the `logging.DEBUG` output configured in `app_licitaia.py`. Tests do not silence logging; let the AppTest run and read the captured output.

## Mocking

**Framework:** None. No `unittest.mock`, no `pytest-mock`, no `monkeypatch` is in use across the suite (verified by grep — zero matches in `tests/`).

**Pattern:**
- Tests run against the **real SQLite DB** at `data/precios.db` (after `init_db()`). Mutating tests restore state in `try/finally`.
- Tests that need specific data construct `ParametrosProyecto` directly with values from the live catálogo (`tests/test_snapshot_excel.py::_hacer_params_referencia`).

**What NOT to mock:**
- Never mock Streamlit widgets — drive them via AppTest.
- Never mock SQLite — use the real DB; the migration chain is fast (~1s).
- Never mock CLIPS — `src/reglas/alertas_clips.py:generar_alertas_tecnicas` is fast enough to call directly.

**What MAY be substituted:**
- Test data dicts via `tests/helpers.py:_resultado_minimal()` for cases that need to insert a "resultado" row in the historial DB without driving the calculator UI end-to-end.

## Fixtures and Factories

**Test data factories:**
```python
# tests/helpers.py
def _app_calculadora() -> AppTest:
    return AppTest.from_file("pages/calculadora.py")

def _calcular_aba(at, *, dn=100, longitud=50.0, profundidad=1.0):
    at.number_input(key="ABAS_longitud").set_value(longitud)
    at.number_input(key="ABAS_profundidad").set_value(profundidad)
    at.selectbox(key="ABAS_diametro").set_value(dn)
    at.run()
    at.button(key="btn_calcular").click().run()
    return at

def _resultado_minimal() -> dict:
    """Dict resultado minimo valido para insertar en DB sin pasar por la UI."""
    return {...}
```

- `tests/helpers.py` is the single shared factory module. Imported as `from helpers import _app_calculadora, _calcular_aba, _calcular_san`.

**Fixtures (pytest):**
- Used sparingly. `tests/test_bd_invariante_ci.py` uses `@pytest.fixture(scope="module")` for `catalogo_oficial` and `precios_bd` so the DB and JSON load only once per module.
- No conftest fixtures shared across files.

**Reference data:**
- `data/catalogo_oficial.json` — JSON snapshot of the official Excel prices, used by `tests/test_bd_invariante_ci.py` to verify the BD × CI = Excel invariant.
- `240415_VALORACIÓN ACTUACIONES.xlsx` — anchor spreadsheet for `tests/test_audit.py`, `tests/test_validacion_excel.py`, and the baseline values in `tests/test_snapshot_excel.py`.

## Coverage

**Requirements:** None enforced. There is no `coverage`/`pytest-cov` configuration, no CI threshold.

**View coverage:**
- Not part of the developer workflow. The implicit "coverage" model is: every UI behaviour is covered by AppTest in `test_calculadora.py` / `test_admin.py` / `test_historial.py`; every domain formula is anchored to Excel in `test_audit.py` / `test_validacion_excel.py` / `test_snapshot_excel.py`; every architectural invariant is enforced via AST tests.

## Test Types

**Behaviour (AppTest) tests:**
- `tests/test_calculadora.py`, `tests/test_admin.py`, `tests/test_historial.py`.
- Drive the page via Streamlit's testing harness, assert via `at.session_state` and `at.exception`.

**Pure-function audit tests:**
- `tests/test_audit.py` — calls `calcular_geometria`, `calcular_resumen`, `materiales_san` directly with anchored values.
- `tests/test_validacion_excel.py` — locks geometry and financial formulas against literal Excel cell values.

**Snapshot tests against Excel:**
- `tests/test_snapshot_excel.py::test_snapshot_valores_financieros` — full `calcular_presupuesto()` baseline (PEM, GG, BI, PBL, IVA, TOTAL) anchored to a reference proyecto with a baseline date stamped in the docstring (`Baseline actualizado 2026-04-27`). When the baseline changes, update the docstring with rationale.
- `tests/test_snapshot_excel.py::test_material_demolicion_afecta_total` — tests **ordering and delta** between material variants instead of point values, robust to small price drift.

**Architectural invariant tests:**
- `tests/test_fronteras_capas.py` — AST walks every `.py` in `src/` and rejects forbidden imports per layer. Excepciones must be added to `_EXCEPCIONES` with justification.
- `tests/test_reglas_estructura.py` — only `src/reglas/alertas_clips.py` may import `clips`.
- `tests/test_aplicacion_estructura.py` — `src/aplicacion/*.py` does not import `streamlit` or `sqlite3`.
- `tests/test_constantes_dominio.py` — literal `1.05` forbidden in `src/infraestructura/precios.py`.

**Sistema experto tests:**
- `tests/test_etiquetas.py` — drives `generar_alertas_tecnicas(...)` with parameter overrides, asserts which `etiqueta` and `alerta` rule_ids fire. Specifically tests **encadenamiento** (1st-level etiqueta → 2nd-level etiqueta → alerta) — this is the TFG defence evidence that the system has real inference, not if/else.

**DB invariant tests:**
- `tests/test_bd_invariante_ci.py` — verifies `BD.precio × 1.05 ≈ Excel.precio_oficial` for every entry in `data/catalogo_oficial.json` (~77 entries). Uses `pytest.xfail` to track known drifts (e.g. `test_deuda_conocida_patron_d`); a passing xfail forces review (XPASS).
- `tests/test_db_estructura.py` — verifies all 16 migrations are present, ordered correctly (M7 before M6 by historical reasons), and `schema_version` reaches 16 after `init_db()`.
- `tests/test_infraestructura_pura.py` — spawns a `subprocess.run(...)` to verify `cargar_precios()` works without Streamlit being importable. Also tests SQLite WAL mode.

**E2E tests:** Not used. AppTest covers the full UI flow within the same process.

## Common Patterns

**Async testing:** N/A (no async code in the project).

**Error testing:**
```python
# Asserting Streamlit surfaces a validation error
at.button[0].click().run()           # entra modo confirmacion
at.button[0].click().run()           # intenta guardar invalido
assert len(at.error) > 0, "Esperado error de validacion al guardar pct_gg=999"

# Asserting DB invariant after a bad attempt
precios_db = cargar_todo()
assert precios_db["pct_gg"] == pytest.approx(0.13, abs=0.001)
```

**Float comparison:**
```python
# Currency / cents
assert r["total"] == pytest.approx(r["pbl_sin_iva"] + r["iva"], abs=0.01)
assert r["pem"] == pytest.approx(58845.26, abs=0.01)

# Geometry / metres
assert geo.ancho_fondo_m == pytest.approx(0.6, abs=1e-4)
```

**Parametrize when shape repeats:**
```python
@pytest.mark.parametrize(
    "overrides,etiqueta_esperada",
    [
        ({"aba_profundidad_m": 4.0}, "zanja-compleja"),
        ({"san_activa": True, "san_profundidad_m": 4.0}, "zanja-compleja"),
        ({"aba_longitud_m": 150.0, "acometidas_aba_n": 10}, "tramo-urbano-denso"),
        ...
    ],
)
def test_etiquetas_primer_nivel(overrides, etiqueta_esperada):
    ...
```

**Asserting CLIPS rule firings via rule_id and etiqueta id:**
```python
def _ids_etiquetas(resultado): return {e["id"] for e in resultado["etiquetas"]}
def _rule_ids_alertas(resultado): return {a["rule_id"] for a in resultado["alertas"]}

assert "zanja-compleja" in _ids_etiquetas(r)
assert "alerta-fibrocemento-sin-gestion" in _rule_ids_alertas(r)
```
This pattern is THE way to assert CLIPS behaviour. Never assert by `msg` text — the lenguaje-llano convention means alert messages may be reworded; their `rule_id` is the contract.

**Restoring DB state after a mutating test:**
```python
gg_original = cargar_todo()["pct_gg"]
try:
    # ... mutating AppTest interactions ...
finally:
    precios_restore = cargar_todo()
    precios_restore["pct_gg"] = gg_original
    guardar_todo(precios_restore)
```

**No emojis in test names, docstrings, or assert messages.** Stay aligned with the project-wide no-emoji convention; differentiate test severity via the test name and module docstring.

---

*Testing analysis: 2026-05-04*
