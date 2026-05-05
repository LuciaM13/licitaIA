# Roadmap: LicitaIA

## Overview

LicitaIA es una herramienta Streamlit ya en uso para presupuestación paramétrica
de redes lineales urbanas EMASESA, con sistema experto CLIPS encadenado y
matemática certificada contra el Excel oficial. Quedan cuatro frentes para
cerrar v1: hacer defendible la inferencia ante tribunal TFG (F3), validar el
catálogo contra obras reales y cerrar gaps por ampliación (F1), permitir crear
variantes inline desde la calculadora sin perder el formulario (F2), y endurecer
tests + UX antes de la defensa (F4). El orden de construcción F3 → F1 → F2 → F4
viene fijado por riesgo (F3 no toca BD, mayor valor defensivo, primera demo)
y dependencias (F2 necesita saber qué falta, lo cual sale de F1).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Trazabilidad del Sistema Experto** - Cadena inferencia visible bajo cada alerta, defendible ante tribunal
- [ ] **Phase 2: Validación y ampliación del catálogo** - Gap analysis 7 obras reales y nuevas variantes en `precios.db`
- [ ] **Phase 3: Creación inline de partidas** - `@st.dialog` junto al selectbox y página admin recortada a configuración
- [ ] **Phase 4: Tests y robustez UX** - AppTest del flujo inline, mensajes legibles, suite limpia para defensa

## Phase Details

### Phase 1: Trazabilidad del Sistema Experto
**Goal**: El técnico (y el tribunal TFG) pueden ver, bajo cada alerta CLIPS, qué inputs activaron qué etiquetas, qué etiquetas dispararon la regla y qué fuente normativa la respalda
**Depends on**: Nothing (first phase)
**Requirements**: SE-01, SE-02, SE-03, SE-04, SE-05, SE-06
**Success Criteria** (what must be TRUE):
  1. Cada presupuesto guardado en historial almacena la cadena de inferencia completa (regla → etiquetas → inputs con valor real → fuente normativa) en la tabla `presupuesto_cadena_inferencia`, consultable vía SQL como evidencia auditable para defensa TFG. La cadena NO se renderiza en la UI de calculadora — las alertas CLIPS ya cumplen ese rol en lenguaje llano; el detalle técnico (rule_id, capa, etiquetas) viviría como ruido para el licitador. Decisión revisada 2026-05-05.
  2. La sección "Validación técnica" de la calculadora se mantiene tal cual: chips de clasificación + `st.error/warning/info` con mensaje del SE en lenguaje llano. Sin expanders ni jerga del motor de reglas.
  3. El módulo `src/reglas/trazabilidad_clips.py` existe, no importa `clips`, y sus tests corren sin clipspy instalado
  4. Si un desarrollador añade una `defrule` en `templates.py` sin entrada en `RULE_PROVENANCE`, el test estructural en CI falla
  5. El presupuesto persistido en historial incluye `cadena_inferencia` sin haber alterado el campo `trazabilidad` previo (compatibilidad hacia atrás)
**Plans**: 4 plans
- [ ] 01-01-PLAN.md — Contratos (CadenaItem) + modulo de provenance estatica (RULE_PROVENANCE + explicar_alerta) + frontera AST
- [ ] 01-02-PLAN.md — Persistencia: migracion m17 + tabla presupuesto_cadena_inferencia + persistir/hidratar en historial.py + tests de estructura BD a 17 migraciones
- [ ] 01-03-PLAN.md — Integracion runtime: extender generar_alertas_tecnicas + ResultadoPresupuesto + UI con st.expander adyacente
- [ ] 01-04-PLAN.md — Tests: SE-05 estructural en test_reglas_estructura, SE-04 AppTest en test_calculadora, SE-06 snapshot en test_historial_snapshot
**UI hint**: yes

### Phase 2: Validación y ampliación del catálogo
**Goal**: Cada una de las 7 obras reales en `data/proyectos_individuales/` está clasificada (in/parcial/out-of-scope) y, para las in-scope, las brechas por capítulo cierran dentro de tolerancia AACE Class 5 vía nuevas variantes en `precios.db` (sin tocar filas existentes)
**Depends on**: Phase 1
**Requirements**: CAT-01, CAT-02, CAT-03, CAT-04, CAT-05, CAT-06, CAT-07
**Success Criteria** (what must be TRUE):
  1. El técnico puede abrir el notebook de `notebook/` y ver, para cada obra, los parámetros derivados directamente del BC3 sin ajustes manuales
  2. La tabla de gap analysis muestra por capítulo y obra: PEM-real, PEM-LicitaIA, gap € y %, y tipo de gap (catalog / formula / scope)
  3. La tolerancia ±15% PEM global / ±20% por capítulo está pre-declarada en el notebook antes de producir la tabla
  4. Cada obra tiene una clasificación documentada (in-scope, parcialmente in-scope, out-of-scope) con motivo explícito
  5. Tras correr nuevas migraciones (m17+) con los ítems faltantes a `precio/1.05`, la tabla re-ejecutada cierra brechas o las clasifica como formula/scope gap
**Plans**: 5 plans
- [ ] 02-01-PLAN.md — Infraestructura: _obras_individuales_helpers.py (loader BC3 + dataclasses + MAPPINGS stubs) + notebook skeleton con tolerancia AACE + data/proyectos_individuales/
- [ ] 02-02-PLAN.md — Clasificacion cualitativa: pasada de las 7 obras, curado de MAPPINGS, tabla in/parcial/out-of-scope en notebook (con checkpoint humano)
- [ ] 02-03-PLAN.md — Gap analysis PRE-migraciones: derivar_parametros implementada, tabla gap por obra y capitulo, catalog gaps identificados
- [ ] 02-04-PLAN.md — Migraciones m18+: un archivo por catalog gap, precios int(round(val/1.05*100)), registradas en MIGRACIONES
- [ ] 02-05-PLAN.md — Cierre: tabla gap POST-migraciones + diff, seccion 4.2 en resultados_tfg.md, 5 assertions en test_db_estructura.py actualizadas, pytest verde

### Phase 3: Creación inline de partidas
**Goal**: El técnico puede crear una nueva variante de catálogo (tubería, acerado, calzada, valvulería, acometida, pozo, imbornal) desde la propia calculadora junto al `selectbox` que falla, sin perder el resto del formulario, y la página de administración queda recortada a porcentajes globales + defaults UI + auditoría drift
**Depends on**: Phase 2
**Requirements**: INL-01, INL-02, INL-03, INL-04, INL-05, INL-06, INL-07, INL-08, INL-09
**Success Criteria** (what must be TRUE):
  1. El técnico abre un diálogo modal junto al selectbox del catálogo que no encuentra, introduce label/red/precio/datos mínimos y, al guardar, el nuevo ítem aparece auto-seleccionado en el selectbox sin recargar la página
  2. Longitud, profundidad, acometidas y resto de campos rellenados antes de abrir el diálogo siguen presentes al cerrarlo (sin state-loss)
  3. Junto al campo de precio aparece la etiqueta "Introduce el precio base EMASESA (sin el margen de seguridad)" y la inserción nunca dispara el `DELETE+INSERT` masivo de `guardar_todo()`
  4. La página antes llamada "Administrar precios" se llama "Configuración y catálogo" y solo contiene porcentajes globales (GG, BI, IVA, factor esponjamiento, pct_ci, pct_manual_defecto), defaults UI y vista de auditoría drift; las tablas editables de partidas han desaparecido
  5. Intentar guardar con label duplicado, campos vacíos o precio ≤ 0 muestra un error claro en el diálogo y no escribe nada en `precios.db`
**Plans**: TBD
**UI hint**: yes

### Phase 4: Tests y robustez UX
**Goal**: El proyecto llega a la defensa con suite verde sobre el estado commiteado, AppTest cubriendo el flujo inline, mensajes de error legibles ante configuraciones inconsistentes, y sin acumulación de estado CLIPS entre reruns rápidos
**Depends on**: Phase 3
**Requirements**: TST-01, TST-02, TST-03, TST-04, TST-05, TST-06
**Success Criteria** (what must be TRUE):
  1. `pytest tests/` corre verde de extremo a extremo sobre el árbol commiteado, incluyendo el invariante CI tras los nuevos ítems de Phase 2
  2. Existe al menos un AppTest que abre el `@st.dialog` inline, inserta una variante vía inyección de `session_state`, cierra y comprueba que el selectbox queda actualizado
  3. Si un catálogo obligatorio está vacío al arrancar, el técnico ve un mensaje legible (no un traceback Python) que le indica qué falta
  4. Tras 10+ interacciones consecutivas en la calculadora (cambios rápidos de longitud, material, acometidas), las alertas y etiquetas siguen siendo coherentes y no quedan facts CLIPS huérfanos
  5. Los tests estructurales (`test_etiquetas.py`, `test_reglas_estructura.py`, fronteras de capas) siguen pasando tras cualquier edición de `templates.py` o de los módulos de reglas
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Trazabilidad del Sistema Experto | 0/4 | Planned | - |
| 2. Validación y ampliación del catálogo | 0/5 | Planned | - |
| 3. Creación inline de partidas | 0/TBD | Not started | - |
| 4. Tests y robustez UX | 0/TBD | Not started | - |
