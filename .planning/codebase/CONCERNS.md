# Codebase Concerns

**Analysis Date:** 2026-05-04

## Tech Debt

**Cambios no commiteados de la refactorización del decisor determinista (working tree sucio):**
- Issue: el working tree contiene una refactorización a medias que renombra el "motor" del SE a "decisor" y separa la lógica de selección de material de las alertas técnicas. Hay borrados (`src/reglas/motor.py`, `src/reglas/trazabilidad.py`) y modificaciones funcionales convivientes en el mismo árbol con nuevos módulos no committeados (`src/reglas/decisor.py`, `src/reglas/explicaciones.py`, `src/reglas/alertas_clips.py`, `src/reglas/templates.py`).
- Files:
  - `src/reglas/motor.py` (BORRADO — `git status: D`)
  - `src/reglas/trazabilidad.py` (BORRADO — `git status: D`)
  - `src/aplicacion/calcular_presupuesto.py` (modificado, sin commit)
  - `src/domain/financiero.py` (modificado, sin commit)
  - `src/presupuesto/bloques.py` (modificado, sin commit)
  - `tests/test_fronteras_capas.py`, `tests/test_reglas_estructura.py`, `tests/test_snapshot_excel.py` (modificados, sin commit)
  - `data/precios.db` (modificado, sin commit)
- Impact: cualquier rebase, cambio de rama o instalación limpia perderá el trabajo. La rama `main` deja de ser un punto recuperable de la app que ejecuta el usuario.
- Verificación de imports rotos: ninguno. `grep` exhaustivo (`from src.reglas.motor` / `from src.reglas.trazabilidad`) en `src/`, `pages/`, `tests/` no devuelve resultados — la migración a `decisor`/`explicaciones` se ha hecho de forma consistente. Las menciones a "motor" en `src/reglas/alertas_clips.py:79`, `src/domain/geometria.py:129`, etc. son solo en docstrings/comentarios, no imports.
- Fix approach: revisar el diff (`git diff`), verificar que los tests modificados pasan, y crear un commit cohesivo "Separación decisor determinista vs alertas CLIPS (cierre Pata 1/Pata 2)". Borrar `src/reglas/motor.py` y `src/reglas/trazabilidad.py` con `git rm`.

**Refactor "ABA materiales fuera de base GG/BI, SAN dentro" sin tests confirmando la división:**
- Issue: la modificación pendiente en `src/aplicacion/calcular_presupuesto.py:200-280` y `src/domain/financiero.py:43-65` introduce dos nuevos contadores `materiales_aba_total` y `materiales_san_total` y cambia la base GG/BI para alinear con el comportamiento del Excel EMASESA (ABA `=SUM(J57:J60)` excluye e), SAN `=SUM(J48:J52)` incluye e). Es un cambio numérico real, no cosmético.
- Files:
  - `src/aplicacion/calcular_presupuesto.py:200-208` (nuevos contadores)
  - `src/aplicacion/calcular_presupuesto.py:268-274` (nueva base = solo materiales ABA)
  - `src/domain/financiero.py:43-65` (docstring actualizado)
  - `src/presupuesto/bloques.py:147-215` (acumulación segregada por red)
- Impact: cambio del PEM/GG/BI para todos los proyectos mixtos ABA+SAN respecto a la versión committeada en `main`. El campo `estado["materiales_total"]` queda sin uso pero sigue presente.
- Fix approach: confirmar con `tests/test_snapshot_excel.py` que los snapshots oficiales EMASESA siguen cuadrando, eliminar el contador `materiales_total` muerto, y commitear como "Fix base GG/BI: solo materiales ABA, alineado con Excel oficial".

**`materiales_total` muerto:**
- Issue: tras el refactor anterior, `estado["materiales_total"]` se acumula en `src/presupuesto/bloques.py:149` y `:211` pero NO se consume en ningún sitio (la base de GG/BI usa `materiales_aba_total` ahora).
- Files: `src/presupuesto/bloques.py:149`, `src/presupuesto/bloques.py:211`, `src/aplicacion/calcular_presupuesto.py:203`
- Impact: campo zombie que confunde al lector.
- Fix approach: eliminar la clave `materiales_total` del dict `estado` y las dos asignaciones.

**Convención CI (pct_ci=1.05) NO es deuda — está documentada y validada:**
- Verificación: el contexto de la tarea sugería que la BD almacenaba precios "ajustados" cuando debería guardar el oficial. Inspección de `src/domain/constantes.py:17-27`, `src/infraestructura/precios.py:194-226` y `src/infraestructura/validacion_oficial.py:1-12` confirma lo contrario: la BD almacena precios BASE (sin CI), y el runtime aplica `pct_ci` (default 1.05) sobre una `deepcopy` para reproducir el Excel oficial. El invariante es `BD.precio × pct_ci(1.05) = Excel oficial`.
- Status: el modelo está bien. El test `tests/test_bd_invariante_ci.py` lo audita continuamente.
- Riesgo residual: la documentación advierte (`src/infraestructura/precios.py:213-216`) que añadir un precio nuevo desde admin requiere meter `valor_Excel / 1.05`, no el valor Excel directo. Si un admin nuevo desconoce esto introducirá una sobrevaloración del 5%. Mitigación parcial: `src/infraestructura/validacion_oficial.detectar_drifts()` avisa con `warning` cuando `|bd × ci − oficial| / oficial > 5 %`.
- Fix approach (mejora): en la UI de admin, añadir un toggle "estoy introduciendo el valor Excel oficial" que aplique `/1.05` antes de guardar, en `pages/admin_precios.py`.

**Datos de presupuesto modificados sin trazabilidad git (`data/precios.db`):**
- Issue: `data/precios.db` aparece como modificado en el working tree. Es un binario SQLite versionado en git por necesidad de Streamlit Cloud (ver `.gitignore` línea con TODO post-docker), por lo que cualquier diff humano es imposible. Mezclado con cambios de código sin commit.
- Files: `data/precios.db` (`git status: M`)
- Impact: imposible saber qué tabla cambió. Si el cambio es accidental (ej. arranque local de la app que actualizó algún registro vía admin) se está perdiendo el estado canónico.
- Fix approach: ejecutar el seed (`data/precios_seed.sql`) sobre una BD limpia y comparar con la modificada (la app debería tener un export estable). Después, cumplir el TODO del `.gitignore`: mover a "seed-on-boot" y dejar de versionar `precios.db`.

**Carpeta `notebook/` sin trackear (`?? notebook/`):**
- Issue: la carpeta contiene utilidades de validación contra Excel oficial (`_excel_helpers.py`, `_inspeccion_excel.py`), un notebook (`08_validacion_excel.ipynb`), un Word (`resultados_tfg.docx`), y un fichero de resultados markdown (`resultados_tfg.md`). El `__pycache__/` referencia un módulo `_bc3_helpers.py` que ya no existe en disco — cache rancia.
- Files: `notebook/` (untracked entero)
- Impact: trabajo de TFG (memoria, validaciones del experto contra BC3, helpers reutilizables) fuera de control de versiones. Pérdida total si se borra el directorio.
- Fix approach: decidir qué versionar (los `.py` y el `.ipynb` sí; los `.docx` y `__pycache__/` no), añadir reglas a `.gitignore` para `notebook/__pycache__/` y `*.docx`, y commitear el resto. El `.gitignore` global ya cubre `*.xlsx` con excepción para `data/*.xlsx`, así que cualquier Excel suelto en `notebook/` se ignorará.

**Tests `xfail` sobre deuda EMASESA conocida (Patrón D):**
- Issue: `tests/test_bd_invariante_ci.py:472-492` marca como `xfail(strict=True)` la deuda del Patrón D (drift ~−4.76 % en valvulería tipo "compuerta"). El TODO referenciado en el reason (`src/infraestructura/db.py _ejecutar_migraciones() final`) apunta a un fichero que ya no existe — `src/infraestructura/db.py` se rompió en `src/infraestructura/db/` (paquete) en el commit `f1862bc`.
- Files: `tests/test_bd_invariante_ci.py:475-476`, migraciones bajo `src/infraestructura/db/migrations/`
- Impact: el TODO está desreferenciado. Quien venga a corregir el Patrón D va a buscar un fichero inexistente.
- Fix approach: actualizar el reason del `xfail` para apuntar al directorio `src/infraestructura/db/migrations/` y aclarar que la migración correctiva sería un nuevo fichero `m17_*.py`.

## Known Bugs

**Doble cláusula `except` redundante en admin_precios:**
- Symptoms: `pages/admin_precios.py:26` declara `except (ValueError, Exception)` — `Exception` ya cubre `ValueError`, por lo que la tupla es ruido.
- Files: `pages/admin_precios.py:26`
- Trigger: estilo, no afecta funcionalidad.
- Workaround: cambiar a `except Exception as e`.

## Security Considerations

**Secrets de Streamlit en archivo .toml local (no commiteado):**
- Risk: `.streamlit/secrets.toml` está correctamente listado en `.gitignore` (línea 28 del `.gitignore`).
- Files: `.streamlit/config.toml` (committeado, solo tema, sin secretos), `.streamlit/secrets.toml` (no presente, gestionado por Streamlit Cloud).
- Current mitigation: `.gitignore` cubre el patrón. La inspección no encontró credenciales hardcodeadas en el código (`grep` sobre `src/` para `os.environ` solo retorna `LICITAIA_AUDIT_ACTOR` en `src/infraestructura/db_precios.py:286`, no es secreto).
- Recommendations: ninguna acción inmediata.

**Inyección SQL vía `f-string` en `DELETE` y `WHERE` (mitigada por whitelist):**
- Risk: `src/infraestructura/db_precios.py:305` ejecuta `conn.execute(f"DELETE FROM {tabla}")` y `src/infraestructura/db/helpers.py:38` ejecuta `f"SELECT {columnas} FROM {tabla} WHERE red=? ORDER BY {orden}"`.
- Files: `src/infraestructura/db_precios.py:305`, `src/infraestructura/db/helpers.py:38`
- Current mitigation: ambos sitios validan `tabla in _TABLAS_PERMITIDAS` antes de interpolar (`src/infraestructura/db_precios.py:303-304`, `src/infraestructura/db/helpers.py:32-33`). `columnas` y `order_by` son literales en código, no input de usuario, y el comentario de `helpers.py:28-31` lo exige explícitamente.
- Recommendations: añadir un test que recorra todos los call-sites de `_cargar_por_red` y verifique que ningún literal viene de input externo. Como mejora futura, considerar `sqlite3.Cursor.execute` con identificadores en lista blanca usando `enum`.

**El test `test_bd_invariante_ci.py:440` interpola `tabla` en SQL:**
- Risk: `f"SELECT COUNT(*) FROM {tabla}"` en código de tests; el valor viene de los parámetros del test (no input externo), así que no es explotable.
- Files: `tests/test_bd_invariante_ci.py:440`
- Current mitigation: input controlado por el propio test.
- Recommendations: ninguna.

**Validación de input en historial: parámetros se serializan como `str(valor)` sin tipado:**
- Risk: `src/aplicacion/historial.py:88` guarda parámetros como string sin validar contenido. La columna es `valor TEXT` así que SQLite lo acepta — pero al recargar (`src/aplicacion/historial.py:158`) no se vuelve a parsear.
- Files: `src/aplicacion/historial.py:84-88`, `src/aplicacion/historial.py:152-158`
- Current mitigation: el dict `parametros` viene del UI Streamlit ya construido (`pages/calculadora.py:633`).
- Recommendations: documentar el contrato (qué claves y tipos esperados) en el docstring de `guardar_presupuesto`.

## Performance Bottlenecks

**`deepcopy` del dict de precios en cada cálculo:**
- Problem: `src/aplicacion/calcular_presupuesto.py:191` ejecuta `copy.deepcopy(precios_base)` en cada llamada para no mutar el dict caller. Sobre el catálogo completo (decenas de listas con cientos de items entre tuberías, valvulería, pozos, demolición, etc.) tiene coste no trivial.
- Files: `src/aplicacion/calcular_presupuesto.py:191`
- Cause: `_aplicar_ci` muta el dict in-place y se quiere evitar contaminar la caché de Streamlit.
- Improvement path: hacer `_aplicar_ci` puro (devolver dict nuevo) o cachear el dict ya con CI aplicado en `src/ui/precios_cache.py` con clave `(hash_db, pct_ci)`.

**`generar_alertas_tecnicas` reconstruye un environment CLIPS por llamada:**
- Problem: `src/reglas/alertas_clips.py:102-156` hace `clips.Environment()` + `env.build` para cada plantilla y cada regla en cada cálculo. CLIPS es pesado de inicializar.
- Files: `src/reglas/alertas_clips.py:102-156`
- Cause: aislamiento entre llamadas (sin estado residual entre ejecuciones).
- Improvement path: si la latencia se nota en UI, cachear el `Environment` ya populado y solo asertar/limpiar el hecho `datos-proyecto` por llamada. Hoy no es crítico (TFG, single-user).

**Re-resolución completa del catálogo CI por cada `_resolver_item_ci`:**
- Problem: `src/aplicacion/calcular_presupuesto.py:51` hace `next(... for i in catalogo if i.get("label") == label)` — O(n) por cada uno de los ~9 items que se re-resuelven en `_reresolver_items_ci`.
- Files: `src/aplicacion/calcular_presupuesto.py:45-96`
- Cause: las listas de catálogo no están indexadas por label.
- Improvement path: si se nota lentitud, construir un `dict[label]→item` por catálogo en `_aplicar_ci`. Hoy es despreciable.

## Fragile Areas

**Acoplamiento por nombre de clave entre dict resultado, BD, y UI ("trazabilidad"):**
- Files: `src/reglas/decisor.py:204`, `src/aplicacion/historial.py:90-98`, `src/infraestructura/db/schema.py:259`, `pages/historial.py:24-285`, `src/domain/tipos.py:166-168`
- Why fragile: la clave `"trazabilidad"` se usa en (1) el dict que devuelve el decisor, (2) el nombre de la tabla `presupuesto_trazabilidad`, (3) el campo del `TypedDict ResultadoPresupuesto`, y (4) las claves de la UI. Se conserva por compatibilidad histórica aunque el contenido ya no viene de un motor de inferencia, solo de explicaciones generadas por `src/reglas/explicaciones.py`. Esto está documentado en `src/reglas/decisor.py:89-92`.
- Safe modification: si se quiere renombrar a "explicaciones", hace falta migración de schema (`presupuesto_trazabilidad` → `presupuesto_explicaciones`), update de todos los call-sites, y migración de datos del historial.
- Test coverage: cubierto por `tests/test_calculadora.py:304-313` y `tests/test_tipos_domain.py:59`. Pero el contrato semántico (qué significa "trazabilidad" en cada uno) no está testado, solo el shape.

**Pipeline CLIPS textual + `_iter_construcciones`:**
- Files: `src/reglas/templates.py` (276 líneas de strings con templates+rules), `src/reglas/alertas_clips.py:32-51`
- Why fragile: las reglas CLIPS se almacenan como strings Python con f-string interpolación de `UMBRALES`. Un fallo de sintaxis o un banner ASCII mal puesto rompe `env.build()` en runtime, no en import. El parser `_iter_construcciones` separa por doble salto de línea — sensible al formato.
- Safe modification: editar reglas CLIPS dentro de `templates.py`, lanzar localmente un cálculo completo (no solo tests unitarios — `tests/test_etiquetas.py:4` documenta la excepción a la estrategia "solo AppTest" para CLIPS) y verificar que `env.run()` no lanza.
- Test coverage: `tests/test_etiquetas.py` (233 líneas) cubre etiquetas y alertas CLIPS exhaustivamente.

**Re-resolución CI con failure modes silentes:**
- Files: `src/aplicacion/calcular_presupuesto.py:62-96`
- Why fragile: si un item del proyecto no se encuentra en el catálogo CI tras aplicar CI, ahora se lanza `ValueError` (fail-fast desde el commit `f1862bc`). Pero `_resolver_item_ci` (`src/aplicacion/calcular_presupuesto.py:45-59`) sigue logueando warning y devolviendo `None`, sin que `_reresolver_items_ci` distinga "no había item" de "lo perdimos".
- Safe modification: cuando se añadan más catálogos a `_reresolver_items_ci`, mantener la guarda fail-fast del wrapper `_ci`.
- Test coverage: `tests/test_fail_fast_precios.py` (presente en el listado, sin inspeccionar línea a línea).

## Scaling Limits

**SQLite single-writer, app multi-usuario:**
- Current capacity: WAL activado (`src/infraestructura/db/connection.py:49`) → múltiples lectores con un único escritor. Suficiente para Streamlit Cloud single-tenant TFG.
- Limit: si la app se despliega a varios licitadores concurrentes editando precios, las escrituras serializan y `guardar_todo()` (que hace `DELETE FROM` + re-insert sobre 17 tablas) bloquea ~cientos de ms.
- Scaling path: postgres + RLS si se monetiza, o split del admin a un proceso batch. Hoy no aplica.

**Snapshot del audit_log se hace fuera de la transacción (race conditions teóricas):**
- Current capacity: el comentario de `src/infraestructura/db_precios.py:280-283` reconoce que `cargar_todo()` previo se ejecuta con conexión propia separada de la transacción de escritura. Riesgo: dos admins editando a la vez podrían capturar snapshots solapados.
- Limit: con un único usuario admin (caso TFG) no aplica.
- Scaling path: mover snapshot dentro de la misma conexión con `BEGIN EXCLUSIVE` (documentado como tarea futura en el propio comentario).

**`guardar_todo()` reescribe TODA la BD en cada salvado del admin:**
- Files: `src/infraestructura/db_precios.py:296-305` (DELETE de 17 tablas), `:317-463` (re-insert).
- Limit: O(filas_totales) por cada save; es absorbe tablas que no cambiaron. Para los catálogos actuales (~cientos de filas) es <100 ms; deja de escalar si los catálogos crecen 10×.
- Scaling path: introducir diff por categoría usando `src/infraestructura/diff_precios.py:calcular_diff` y emitir solo INSERT/UPDATE/DELETE de los cambios reales. Beneficio adicional: simplifica el `audit_log`.

## Dependencies at Risk

**`clipspy` (compilación nativa, ecosistema reducido):**
- Risk: `clipspy>=1.0.6,<2.0` es una librería de bindings Python a CLIPS (motor experto C de los 80). El `Dockerfile:18-22` instala `build-essential` para compilar wheels cuando PyPI no sirve binario. Comunidad pequeña, releases poco frecuentes.
- Impact: si `clipspy` deja de mantenerse, las alertas técnicas se quedan sin motor. La parte determinista (decisor en `src/reglas/decisor.py`) seguiría funcionando.
- Migration plan: no es realista migrar a otro motor experto sin reescribir `src/reglas/templates.py` desde cero. La defensa del TFG (Pata 2 = CLIPS con inferencia encadenada) está acoplada al motor.

**Streamlit `>=1.38,<2.0`:**
- Risk: el proyecto usa `st.navigation` (≥1.36), `st.logo` (≥1.37), `st.cache_data`. Streamlit ha hecho breaking changes en cada major histórico.
- Impact: una actualización mayor (2.0) podría requerir refactor de páginas y caches.
- Migration plan: pinning está bien. Re-evaluar al saltar a 2.0 si Anthropic/Streamlit publican.

## Missing Critical Features

**No hay export del presupuesto a Excel/PDF para entregar al licitador:**
- Problem: el resultado se muestra en UI y se guarda en BD; no hay exportador al formato oficial EMASESA Excel.
- Blocks: caso de uso real "el licitador descarga el presupuesto y lo presenta a EMASESA".
- Verificación parcial: `notebook/_excel_helpers.py:1-30` lee Excel oficial pero solo para validación contra LicitaIA — no escribe.

**El admin no avisa sobre la convención CI antes de meter precios:**
- Problem: si el admin introduce el precio Excel oficial directamente (sin dividir por 1.05), genera sobrevaloración del 5 %. Hoy `validacion_oficial.detectar_drifts()` lo avisa después; sería preferible prevenir.
- Files: `pages/admin_precios.py`, `src/infraestructura/validacion_oficial.py:46-138`
- Blocks: usabilidad correcta para nuevos admins. Documentado en `src/infraestructura/precios.py:213-216`.

**Sistema experto sin endpoint propio para defenderlo independientemente del cálculo:**
- Problem: las alertas CLIPS (`src/reglas/alertas_clips.generar_alertas_tecnicas`) se invocan desde el flujo de cálculo y la UI, pero no hay un punto de entrada limpio "ejecuta el SE sobre estos parámetros y devuélveme etiquetas+alertas" para demos del TFG.
- Blocks: la defensa de la Pata 2 (CLIPS) en el TFG. La función pública existe (`src/reglas/alertas_clips.py:58`) pero no hay UI o CLI dedicada para mostrarla aislada del presupuesto numérico.
- Verificación: ningún `streamlit run` o entry-point dedicado al SE.

**Pendiente del audit matemático: BD ↔ Excel:**
- Problem: la matemática del código contra Excel está cerrada (memoria del proyecto), pero los gaps remanentes viven en la BD. El test `test_bd_invariante_ci.py` cubre el invariante general pero no enumera todos los conceptos del Excel oficial.
- Blocks: certificación completa del TFG. El xfail del Patrón D es el único gap "tracked"; puede haber más en valvulería/imbornales/acometidas no auditados aún.
- Files: `data/catalogo_oficial.json` (ground truth Excel), `src/infraestructura/validacion_oficial.py` (detector de drift), `tests/test_bd_invariante_ci.py:465-492` (Patrón D xfail).

## Test Coverage Gaps

**`pct_ci` overrides en cálculo:**
- What's not tested: si el licitador cambia `pct_ci` (margen de seguridad) en runtime, ¿el resultado escala correctamente? El test `tests/test_bd_invariante_ci.py` valida `pct_ci=1.05` (default), pero no parametriza otros valores como 1.0 (sin margen) o 1.10.
- Files: `src/infraestructura/precios.py:194-280` (escalado), `pages/calculadora.py:634` (override en UI).
- Risk: silenciosa sobre/infravaloración si el escalado tiene un bug en los catálogos `_CI_DICTS`.
- Priority: Media — afecta una feature de producto explícita (margen configurable).

**Refactor "ABA fuera, SAN dentro" sin test específico parametrizado:**
- What's not tested: el comportamiento exacto del cambio en `src/aplicacion/calcular_presupuesto.py:268-274` (solo materiales ABA en la base). Los snapshots Excel cubren casos puros (solo ABA o solo SAN), pero no necesariamente proyectos mixtos donde la diferencia entre `materiales_total` y `materiales_aba_total` es no nula.
- Files: `src/aplicacion/calcular_presupuesto.py:200-274`, `src/domain/financiero.py:43-65`
- Risk: regresión silenciosa en proyectos mixtos.
- Priority: Alta — el cambio numérico está sin commitear y podría romper presupuestos reales.

**Cobertura del SE encadenado (CLIPS etiquetas → alertas):**
- What's not tested: la propiedad clave de la Pata 2 del TFG es la inferencia encadenada (etiqueta dispara alerta). `tests/test_etiquetas.py` valida etiquetas aisladas, pero la cobertura específica de "alerta X depende de etiqueta Y emitida por regla Z" no está enumerada exhaustivamente.
- Files: `tests/test_etiquetas.py`, `src/reglas/templates.py:30-276`
- Risk: defensas del TFG donde una regla encadenada no dispara y no hay test que lo detecte.
- Priority: Media — crítico para el TFG, no para producción.

**Acceso concurrent admin (escritura simultánea):**
- What's not tested: comportamiento cuando dos pestañas Streamlit guardan a la vez. `src/infraestructura/db_precios.py:280-283` admite que el snapshot pre-cambios queda fuera de la transacción.
- Files: `src/infraestructura/db_precios.py:284-481`
- Risk: audit_log inconsistente si ocurre la race.
- Priority: Baja — caso TFG single-user.

**`pages/calculadora.py` y `pages/admin_precios.py` (los dos ficheros más grandes con UI ~669 líneas):**
- What's not tested: lógica de UI (Streamlit) está parcialmente cubierta por `tests/test_calculadora.py` (740 líneas) y `tests/test_admin.py` (251 líneas), pero los caminos de error (`except Exception` en `pages/calculadora.py:641, 665`, doble cláusula en `pages/admin_precios.py:26`) no parecen ejercitados.
- Files: `pages/calculadora.py:641-649`, `pages/admin_precios.py:24-32`
- Risk: experiencia de usuario en condiciones de error.
- Priority: Baja.

---

*Concerns audit: 2026-05-04*
