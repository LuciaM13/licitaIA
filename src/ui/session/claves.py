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

RESULTADO = "resultado"
"""Último ``ResultadoPresupuesto`` calculado. Persiste entre reruns para
que el botón "Guardar en historial" encuentre el dict sin recalcular."""

HISTORIAL_DESC = "_historial_desc"
HISTORIAL_PARAMS = "_historial_params"
HISTORIAL_PCT_CI = "_historial_pct_ci"
HISTORIAL_CONFIRMAR_GUARDADO = "_historial_confirmar_guardado"


# ---------------------------------------------------------------------------
# Admin precios — flujo de edición con confirmación
# ---------------------------------------------------------------------------

CONFIRMAR_GUARDADO = "confirmar_guardado"
PRECIOS_ORIGINALES = "precios_originales"
PRECIOS_PENDIENTES = "precios_pendientes"


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
INLINE_CREATE_CONFIRMAR = "inline_create_confirmar"
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


# ---------------------------------------------------------------------------
# Calculadora — watchdog de cierre del @st.dialog inline
#
# Streamlit 1.56 envuelve `@st.dialog` en un `_fragment` implícito y
# `on_dismiss` se ejecuta como fragment-rerun (issue streamlit/streamlit
# #12546). Cuando el usuario cierra con la X, navega a otra página o
# refresca, `INLINE_CREATE_TARGET` queda colgado y cualquier rerun
# posterior reabre el dialog. Estos contadores detectan el desfase y
# limpian el target. NO setear directamente: usar los helpers
# `arm_inline_dialog` / `disarm_inline_dialog`.
# ---------------------------------------------------------------------------

INLINE_DIALOG_ARMED = "_inline_dialog_armed"
"""``True`` solo durante el rerun en que se ABRE el dialog (lo arma el
botón "+"). El cuerpo del dialog lo baja a ``False`` al renderizarse."""

INLINE_DIALOG_OPEN_TICK = "_inline_dialog_open_tick"
"""Contador monótono que incrementa cada vez que un botón "+" arma el
dialog. El cuerpo del dialog copia este valor en ``RENDER_TICK`` la
primera vez que se renderiza."""

INLINE_DIALOG_RENDER_TICK = "_inline_dialog_render_tick"
"""Último ``OPEN_TICK`` que el cuerpo del dialog ha confirmado
renderizar. Si ``OPEN_TICK > RENDER_TICK`` y ``ARMED is False``, el
dialog se cerró sin pasar por ``on_dismiss`` y el watchdog limpia
``INLINE_CREATE_TARGET`` automáticamente."""


def arm_inline_dialog(state, target: str) -> None:
    """Arma el dialog inline: setea target, marca ARMED y avanza OPEN_TICK.

    Llamar SIEMPRE desde los handlers del botón "+" en lugar de escribir
    ``state[INLINE_CREATE_TARGET] = target`` directamente; el watchdog
    depende de la sincronía entre las 3 claves.
    """
    state[INLINE_CREATE_TARGET] = target
    state[INLINE_DIALOG_ARMED] = True
    state[INLINE_DIALOG_OPEN_TICK] = state.get(INLINE_DIALOG_OPEN_TICK, 0) + 1


def disarm_inline_dialog(state) -> None:
    """Limpieza idempotente del estado del dialog inline.

    Borra TARGET, CONFIRMAR y ARMED. Los contadores OPEN_TICK / RENDER_TICK
    se preservan (son monótonos): el siguiente arming los volverá a poner
    en sincronía.
    """
    state.pop(INLINE_CREATE_TARGET, None)
    state.pop(INLINE_CREATE_CONFIRMAR, None)
    state.pop(INLINE_DIALOG_ARMED, None)
