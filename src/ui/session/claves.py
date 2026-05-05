"""Constantes de claves de ``st.session_state`` usadas por las páginas.

Cualquier clave que se acceda desde más de un punto (otro fichero, otro
rerun, otro bloque condicional) se declara aquí. Evita la clase de bugs
típica de Streamlit donde un typo en un string no lanza ``KeyError``
sino que devuelve ``None`` silenciosamente.

Las claves que son puramente ``key=`` de un widget Streamlit (leídas solo
por el propio widget en el mismo rerun) pueden quedar como literales; no
aportan riesgo porque el framework las maneja.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Calculadora — flujo de cálculo de presupuesto
# ---------------------------------------------------------------------------

INSTALACION_VALVULERIA = "instalacion_valvuleria"
DESMONTAJE_TIPO = "desmontaje_tipo"
PCT_MANUAL_PCT = "pct_manual_pct"
PCT_MANUAL_AUTO_LAST = "_pct_manual_auto_last"

RESULTADO = "resultado"
"""Último ``ResultadoPresupuesto`` calculado. Persiste entre reruns para
que el botón "Guardar en historial" encuentre el dict sin recalcular."""

HISTORIAL_DESC = "_historial_desc"
HISTORIAL_PARAMS = "_historial_params"
HISTORIAL_PCT_CI = "_historial_pct_ci"


# ---------------------------------------------------------------------------
# Admin precios — flujo de edición con confirmación
# ---------------------------------------------------------------------------

CONFIRMAR_GUARDADO = "confirmar_guardado"
PRECIOS_ORIGINALES = "precios_originales"
PRECIOS_PENDIENTES = "precios_pendientes"
CONFIRMAR_DRIFT_CRITICO = "confirmar_drift_critico"


# ---------------------------------------------------------------------------
# Historial — paginación y detalle
# ---------------------------------------------------------------------------

HIST_PAGE = "hist_page"
VER_DETALLE_ID = "ver_detalle_id"


# ---------------------------------------------------------------------------
# Calculadora — creación inline de partidas (Phase 3)
# ---------------------------------------------------------------------------

INLINE_CREATE_TARGET = "inline_create_target"
"""Identificador del catálogo que el usuario está creando ahora mismo
(``"tuberias_aba"``, ``"acerados"``, …). Se setea al pulsar el botón
"+" junto al ``selectbox``, lo lee la función decorada con
``@st.dialog`` para saber qué formulario renderizar. Se limpia con
``pop`` al cancelar el modal o tras el rerun post-INSERT exitoso."""

INLINE_CREATE_RESULT = "inline_create_result"
"""Payload one-shot tras un INSERT exitoso: tupla
``(tabla, red, label)`` (o ``(tabla, red, tipo)`` para acometidas).

Lo escribe el callback del diálogo tras un INSERT correcto, lo lee el
``selectbox`` correspondiente en el rerun siguiente para fijar su
``index=`` al nuevo item recién creado. Se borra (one-shot) al final
del render de la calculadora vía ``_consumir_inline_result`` —no en
cada selectbox individualmente—para que no haya carrera entre
selectboxes que comparten el resultado.

Se identifica por ``(tabla, red, label)`` y NO por ``id`` porque
``cargar_todo`` no expone los IDs de fila al diccionario de precios
(Riesgo 6 de PATTERNS.md): la UI sólo conoce labels."""
