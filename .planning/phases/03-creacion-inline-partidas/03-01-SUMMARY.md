---
phase: 03-creacion-inline-partidas
plan: 01
subsystem: aplicacion + infraestructura
tags: [phase-3, inline-create, use-case, audit-log, schema-derived]
requires: []
provides:
  - "src.aplicacion.editar_catalogo.insertar_variante_catalogo"
  - "src.aplicacion.editar_catalogo._TABLAS_CON_RED"
  - "src.aplicacion.editar_catalogo._CLAVES_UNICIDAD"
  - "src.infraestructura.db_precios.insertar_fila_catalogo"
  - "src.infraestructura.db_precios.escribir_audit_evento"
  - "src.infraestructura.db_precios._TABLAS_INLINE_EDITABLES"
  - "src.ui.session.claves.INLINE_CREATE_TARGET"
  - "src.ui.session.claves.INLINE_CREATE_RESULT"
affects:
  - "pages/calculadora.py (Plan 03-02 consumirá insertar_variante_catalogo via @st.dialog)"
  - "pages/admin_precios.py (Plan 03-03 recortará tablas editables)"
tech_stack_added: []
tech_stack_patterns:
  - "INSERT-único parametrizado con whitelist de tablas (T-03-06 mitigation)"
  - "Validaciones de negocio en use case + delegación a infraestructura"
  - "Constantes derivadas del schema (no asunciones uniformes) — BLOCK 2/3 fix"
key_files_created:
  - tests/test_editar_catalogo_inline.py
key_files_modified:
  - src/aplicacion/editar_catalogo.py
  - src/infraestructura/db_precios.py
  - src/ui/session/claves.py
decisions:
  - "FLAG 7: insertar_variante_catalogo devuelve int (lastrowid) — la UI lo ignora; existe para logs/audit/tests."
  - "BLOCK 2: clave de unicidad es propia de cada catálogo (tuberias=(red,label), acometidas=(red,tipo), bordillos=(label,), pozos=()), no asunción uniforme (label,red)."
  - "BLOCK 3: red obligatoria sólo para tablas con red NOT NULL (tuberias, acerados, acometidas); rechazada para las demás (valvuleria, bordillos, calzadas, imbornales) porque la columna no existe."
  - "Convención del CI: el use case persiste BASE EMASESA en céntimos; NO pre-multiplica por 1.05. El cargador aplica aplicar_ci en runtime."
  - "Whitelist _TABLAS_INLINE_EDITABLES más restrictiva que _TABLAS_PERMITIDAS: excluye config, defaults_ui, audit_log, presupuestos*, demolicion, entibacion, subbases, desmontaje, pozos_existentes_precios."
metrics:
  duration_min: 25
  completed: 2026-05-05
  tasks_total: 2
  tasks_done: 2
  tests_added: 16
  files_modified: 3
  files_created: 1
---

# Phase 3 Plan 01: Use case y claves session_state para creación inline — Summary

**One-liner:** API pública `insertar_variante_catalogo` (use case) + `insertar_fila_catalogo` / `escribir_audit_evento` (infraestructura) para crear UNA variante de catálogo desde la calculadora con validaciones derivadas del schema y trazabilidad en `audit_log`, sin destruir la invariante CI 141/141.

## Objective recap

Aislar la lógica de INSERT-único, validación y `audit_log` de la UI Streamlit. Sentar la base no-UI sobre la que los Plans 02/03 montarán el `@st.dialog` y el dispatcher inline en `pages/calculadora.py`. Cumplir frontera de capas (use case sin import de Streamlit) y la Convención del CI (precio BASE en céntimos).

## What was built

### 1. Infraestructura — `src/infraestructura/db_precios.py`

| Símbolo | Tipo | Comentario |
|---|---|---|
| `_TABLAS_INLINE_EDITABLES` | `frozenset[str]` | Whitelist restrictiva de catálogos editables inline (8 tablas: tuberias, valvuleria, acometidas, acerados, bordillos, calzadas, pozos, imbornales). |
| `escribir_audit_evento(conn, categoria, clave, operacion, antes_json, despues_json, actor)` | función pública | Wrapper de 1 evento sobre el helper privado `_escribir_audit_log`. No commit; el caller maneja la transacción. |
| `insertar_fila_catalogo(tabla, item, actor="usuario_inline", path=None) -> int` | función pública | INSERT parametrizado dinámico (cols vienen del item, valores por placeholders `?`). Convierte campos `_CAMPOS_MONETARIOS[tabla]` a céntimos vía `_eur_a_cents`. Registra el evento en `audit_log` con actor. Devuelve `lastrowid`. |

### 2. Aplicación — `src/aplicacion/editar_catalogo.py`

| Símbolo | Tipo | Comentario |
|---|---|---|
| `_TABLAS_CON_RED` | `frozenset[str]` | `{"tuberias", "acerados", "acometidas"}` — schema declara `red NOT NULL`. |
| `_CLAVES_UNICIDAD` | `Mapping[str, tuple[str, ...]]` | Clave por catálogo (BLOCK 2 fix); ver tabla más abajo. |
| `insertar_variante_catalogo(tabla, red, item, actor="usuario_inline") -> int` | función pública | Use case con 5 validaciones bloqueantes; delega INSERT en infraestructura. |

### 3. Session-state — `src/ui/session/claves.py`

- `INLINE_CREATE_TARGET = "inline_create_target"` — qué catálogo está siendo creado.
- `INLINE_CREATE_RESULT = "inline_create_result"` — payload one-shot tras INSERT.

## `_TABLAS_CON_RED` y `_CLAVES_UNICIDAD` (derivados del schema real)

Fuente única de verdad: `src/infraestructura/db/schema.py`. **No** se asume uniformidad `(label, red)`.

| Tabla | red NOT NULL | clave de unicidad | Notas |
|---|---|---|---|
| `tuberias` | sí | `("red", "label")` | UNIQUE(red, label) en schema. |
| `acerados` | sí | `("red", "label")` | UNIQUE(red, label) en schema. |
| `acometidas` | sí | `("red", "tipo")` | NO usa label; UNIQUE(red, tipo). |
| `valvuleria` | no | `("label",)` | label TEXT NOT NULL UNIQUE. |
| `bordillos` | no | `("label",)` | label TEXT NOT NULL UNIQUE. |
| `calzadas` | no | `("label",)` | label TEXT NOT NULL UNIQUE. |
| `imbornales` | no | `("label",)` | label TEXT NOT NULL UNIQUE. |
| `pozos` | nullable | `()` | sin UNIQUE en schema; el use case acepta duplicados (no chequea). |

Implicaciones operativas:

- `tabla in _TABLAS_CON_RED` y `red is None` → `ValueError("red es obligatorio para tabla {tabla}")`.
- `tabla not in _TABLAS_CON_RED` y `red is not None` → `ValueError("tabla {tabla} no admite red")` (la columna no existe; pasarla rompería el INSERT).
- Para `pozos`, la UI puede insertar varias filas con el mismo `label` y diferente `intervalo` — comportamiento intencional (catálogo SAN graduado por profundidad).

## Tests creados (`tests/test_editar_catalogo_inline.py`)

16 tests, todos verde (RED → GREEN sin REFACTOR — el código ya estaba en su forma mínima viable).

### Tarea 1 — infraestructura

| # | Test | Verifica |
|---|---|---|
| 1 | `test_1_insertar_fila_catalogo_ok` | INSERT en acerados ABA devuelve `lastrowid > 0`; fila persiste con red/label/unidad esperados. |
| 2 | `test_2_insertar_fila_catalogo_persiste_centimos` | precio=12.34 EUR → 1234 céntimos en BD (sin pre-CI). |
| 3 | `test_3_insertar_fila_catalogo_tabla_no_permitida` | `tabla="presupuestos"` → `ValueError` ("no editable inline"). |
| 4 | `test_4_escribir_audit_evento_anade_una_fila` | audit_log +1 fila con actor="usuario_inline", operacion="INSERT", antes_json=NULL. |

### Tarea 2 — use case

| # | Test | Verifica |
|---|---|---|
| 5 | `test_5_insertar_variante_catalogo_ok_acerados` | Caso feliz: ABA + label/unidad/precio → fila persiste con `precio=1839` y audit_log +1 con actor correcto. |
| 6 | `test_6_validacion_label_vacio` | label="" en acerados → `ValueError` que menciona "label". |
| 7 | `test_7_validacion_precio_no_positivo` | `precio=0` → `ValueError` que menciona "precio". |
| 8a | `test_8a_duplicado_tuberias` | dos INSERT con (red,label) iguales → 2º lanza "ya existe". |
| 8b | `test_8b_duplicado_acometidas` | dos INSERT con (red,tipo) iguales → 2º lanza "ya existe". |
| 8c | `test_8c_duplicado_bordillos_solo_label` | dos INSERT con misma `label` y distinto `unidad` → 2º lanza (clave es solo `(label,)`). |
| 8d | `test_8d_pozos_no_chequea_duplicado` | dos INSERT con misma `label` en pozos → ambos OK (clave vacía). |
| 9a | `test_9a_red_obligatoria_para_tuberias` | tuberias + red=None → `ValueError` que menciona "red" y "tuberias". |
| 9b | `test_9b_red_prohibida_para_valvuleria` | valvuleria + red="ABA" → `ValueError` ("no admite red"). |
| 9c | `test_9c_acometidas_red_obligatoria_ok` | acometidas + red="ABA" + tipo válido → INSERT OK. |
| 10 | `test_10_precio_centimos_no_doble_conversion` | precio=18.39 → 1839 (NO 1929 ni 1932 que indicarían pre-CI). |
| 11 | `test_11_use_case_no_importa_streamlit` | Tras `import src.aplicacion.editar_catalogo`, `streamlit not in sys.modules` (frontera capas en runtime). |

Patrón usado: BD temporal por test vía `tmp_path` + `shutil.copy(_BD_REAL)`. `monkeypatch.setattr(connection, "DB_PATH", bd_temporal)` para que el use case (que llama a `conectar()` sin path en el chequeo de duplicado) lea de la BD del test.

## Verificación CI 141/141

`pytest tests/test_bd_invariante_ci.py -q` antes y después del plan: idéntico (160 passed, 4 skipped, 2 xfailed sobre la suite combinada). Como el use case **no** se invoca en `cargar_todo`, ni añade filas a `data/precios.db` (los tests usan BD temporal), la matemática certificada queda intacta.

```
160 passed, 4 skipped, 2 xfailed in 0.69s
```

`pytest tests/test_fronteras_capas.py -q`: verde — `editar_catalogo.py` no importa `streamlit` (verificado por AST y por test 11 en runtime).

`pytest tests/test_aplicacion_estructura.py -q`: verde — los use cases anteriores siguen accesibles, contrato `ResultadoPreparacion` estable, `editar_catalogo.py` no importa streamlit.

## Mitigaciones del threat register aplicadas

| ID | Mitigación |
|---|---|
| T-03-01 (SQL injection) | INSERT 100 % parametrizado con `?`; columnas vienen del item validado contra `_CAMPOS_MONETARIOS[tabla]`; `tabla` validada contra whitelist. |
| T-03-02 (doble INSERT) | `SELECT 1 ... LIMIT 1` con `_CLAVES_UNICIDAD[tabla]` específica por catálogo. ValueError si existe. |
| T-03-03 (repudio) | Actor `"usuario_inline"` queda en `audit_log` append-only. |
| T-03-06 (privilege elevation) | Whitelist `_TABLAS_INLINE_EDITABLES` (8 tablas), distinta de `_TABLAS_PERMITIDAS` (que incluye historial y config). |
| T-03-07 (doble CI) | Tests 2 y 10 verifican que precio se persiste como BASE en céntimos. |
| T-03-08 (frontera) | Test 11 verifica en runtime; test_fronteras_capas.py por AST. |
| T-03-08b (schema mismatch) | `_TABLAS_CON_RED` filtra antes del INSERT; tabla 9b cubre. |

## Deviations from Plan

Ninguna desviación material. El plan se ejecutó tal cual. Notas menores:

- **Test 11 (frontera streamlit en runtime):** la nota del plan sugería `monkeypatch.delitem(sys.modules, 'streamlit', raising=False)` antes del import. La implementación usa `sys.modules.pop("streamlit", None)` + `sys.modules.pop("src.aplicacion.editar_catalogo", None)` para forzar reimport limpio del módulo bajo prueba. Equivalente funcional; el patrón `pop` no requiere fixture `monkeypatch`. (Rule 3 — issue blocking si streamlit ya estaba cargado por otro test del run.)
- **Tests 5–10 con `monkeypatch.setattr(connection, "DB_PATH", bd_temporal)`:** el plan no lo prescribía explícitamente, pero el chequeo de duplicado en el use case llama a `conectar()` **sin path** (acepta default), por lo que sin el `monkeypatch` los SELECT de duplicado leerían `data/precios.db` real y los tests 8a/8b podrían no detectar duplicados creados en la BD temporal. (Rule 3 — fix necesario para que los tests del plan reflejen la realidad de la API: el use case toma path implícito de `connection.DB_PATH`.) `insertar_fila_catalogo` sí acepta `path=` explícito (tests 1–4 lo usan así); el use case no lo expone porque la UI no lo necesita.

## Known Stubs

Ninguno. Las dos claves session_state (`INLINE_CREATE_TARGET`, `INLINE_CREATE_RESULT`) están declaradas con docstring pero **no** consumidas todavía: las consume el Plan 03-02 (`@st.dialog`) y el Plan 03-03 (rerun + selectbox). Esta separación es intencional — el plan declara el contrato de session-state que los planes siguientes implementan, y `claves.py` es un módulo declarativo (no ejecuta nada al importarse).

## Self-Check: PASSED

Verificación física tras escribir el SUMMARY:

- `src/aplicacion/editar_catalogo.py` modificado — FOUND (use case + constantes nuevas).
- `src/infraestructura/db_precios.py` modificado — FOUND (2 funciones públicas + whitelist).
- `src/ui/session/claves.py` modificado — FOUND (2 claves + docstrings).
- `tests/test_editar_catalogo_inline.py` creado — FOUND (16 tests).
- Commit `5b9acd1` (RED) — FOUND.
- Commit `3e89563` (GREEN T1) — FOUND.
- Commit `b4b60c7` (GREEN T2) — FOUND.
- Smoke `python -c "from src.aplicacion.editar_catalogo import ..."` — imprime `ok`.
