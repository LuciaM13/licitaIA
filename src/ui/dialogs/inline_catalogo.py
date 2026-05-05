"""Dialog inline para crear nuevas variantes de catálogo desde la calculadora.

Patrón Streamlit: ``@st.dialog`` (introducido en Streamlit 1.34+). Hard limit
del framework: solo 1 ``@st.dialog`` puede invocarse por script run; por eso
este módulo expone UNA sola función decorada con ``@st.dialog`` y dispatcha
internamente por ``INLINE_CREATE_TARGET``.

Documentación de referencia:
https://docs.streamlit.io/develop/api-reference/execution-flow/st.dialog

Frontera de capas: este módulo vive en ``src/ui/`` y SÍ puede importar
``streamlit``. El use case de inserción (``insertar_variante_catalogo``)
queda en ``src/aplicacion/editar_catalogo.py`` sin tocar Streamlit, según
``tests/test_fronteras_capas.py``.

Convención del CI (memoria de proyecto): los sub-formularios devuelven el
precio como ``float`` en EUR. El use case del Plan 01 invoca
``_eur_a_cents`` exactamente UNA vez al persistir. NO se debe hacer doble
conversión a céntimos en este módulo.
"""

from __future__ import annotations

import logging

import streamlit as st

from src.aplicacion.editar_catalogo import insertar_variante_catalogo
from src.ui.precios_cache import cargar_precios
from src.ui.session import claves as sk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapeo target -> (tabla, red)
# ---------------------------------------------------------------------------
# Derivado de src/infraestructura/db/schema.py. La regla de `red` la fija el
# schema: red NOT NULL en {tuberias, acerados, acometidas}; ausente o nullable
# en el resto. Para `acerados` se separan dos targets (acerados_aba/acerados_san)
# en simetría con tuberias_*/acometidas_* y para que el dispatcher pueda
# inyectar `red` directamente sin selectbox interno (BLOCK 3 fix del plan).
_TARGET_A_TABLA: dict[str, tuple[str, str | None]] = {
    "tuberias_aba":   ("tuberias",   "ABA"),
    "tuberias_san":   ("tuberias",   "SAN"),
    "valvuleria":     ("valvuleria", None),
    "acometidas_aba": ("acometidas", "ABA"),
    "acometidas_san": ("acometidas", "SAN"),
    "acerados_aba":   ("acerados",   "ABA"),
    "acerados_san":   ("acerados",   "SAN"),
    "bordillos":      ("bordillos",  None),
    "calzadas":       ("calzadas",   None),
    "pozos":          ("pozos",      None),  # red NULLABLE en schema; v1 inline = None
    "imbornales":     ("imbornales", None),
}


# ---------------------------------------------------------------------------
# Dialog público (UN solo @st.dialog del repo)
# ---------------------------------------------------------------------------

@st.dialog("Nueva variante de catálogo", width="large")
def render_inline_create_dialog() -> None:
    """Renderiza el formulario inline de creación de variantes de catálogo.

    Lee ``st.session_state[sk.INLINE_CREATE_TARGET]`` para saber qué catálogo
    está creando el usuario. Despacha al sub-formulario correcto. Tras
    'Guardar' exitoso: invalida caché, propaga resultado one-shot y rerun.
    Tras 'Cancelar': pop del target + rerun (cero side effects sobre la BD).
    """
    target = st.session_state.get(sk.INLINE_CREATE_TARGET)
    if target not in _TARGET_A_TABLA:
        st.error(f"Catálogo desconocido: {target!r}")
        if st.button("Cerrar", key="_inline_cerrar_unknown"):
            st.session_state.pop(sk.INLINE_CREATE_TARGET, None)
            st.rerun()
        return

    tabla, red = _TARGET_A_TABLA[target]
    st.caption(f"Tabla: {tabla}" + (f" - Red: {red}" if red else ""))

    item = _dispatch_form(target)

    col_g, col_c = st.columns([1, 1])
    with col_g:
        guardar = st.button(
            "Guardar",
            type="primary",
            use_container_width=True,
            key=f"_inline_guardar_{target}",
        )
    with col_c:
        cancelar = st.button(
            "Cancelar",
            use_container_width=True,
            key=f"_inline_cancelar_{target}",
        )

    if cancelar:
        st.session_state.pop(sk.INLINE_CREATE_TARGET, None)
        st.rerun()

    if guardar:
        try:
            insertar_variante_catalogo(tabla, red, item, actor="usuario_inline")
        except ValueError as exc:
            st.error(str(exc))
            return  # NO rerun: deja el dialog abierto con el form rellenado.
        # Éxito.
        # Para acometidas la "etiqueta" identificadora es 'tipo' (no hay label).
        etiqueta = item.get("label") or item.get("tipo") or ""
        cargar_precios.clear()
        st.session_state[sk.INLINE_CREATE_RESULT] = (tabla, red, etiqueta)
        st.session_state.pop(sk.INLINE_CREATE_TARGET, None)
        logger.info(
            "inline_create OK -> tabla=%s, red=%s, etiqueta=%s",
            tabla, red, etiqueta,
        )
        st.rerun()


# ---------------------------------------------------------------------------
# Dispatcher de sub-formularios
# ---------------------------------------------------------------------------

def _dispatch_form(target: str) -> dict:
    """Despacha al sub-formulario `_form_*` que corresponde al `target`."""
    dispatch = {
        "tuberias_aba":   _form_tuberias_aba,
        "tuberias_san":   _form_tuberias_san,
        "valvuleria":     _form_valvuleria,
        "acometidas_aba": _form_acometidas,
        "acometidas_san": _form_acometidas,
        "acerados_aba":   _form_acerados,
        "acerados_san":   _form_acerados,
        "bordillos":      _form_bordillos,
        "calzadas":       _form_calzadas,
        "pozos":          _form_pozos,
        "imbornales":     _form_imbornales,
    }
    fn = dispatch.get(target)
    if fn is None:
        return {}
    return fn()


# ---------------------------------------------------------------------------
# Sub-formularios (stubs — implementación real en Tarea 2)
# ---------------------------------------------------------------------------

def _form_tuberias_aba() -> dict:
    return {}


def _form_tuberias_san() -> dict:
    return {}


def _form_valvuleria() -> dict:
    return {}


def _form_acometidas() -> dict:
    return {}


def _form_acerados() -> dict:
    return {}


def _form_bordillos() -> dict:
    return {}


def _form_calzadas() -> dict:
    return {}


def _form_pozos() -> dict:
    return {}


def _form_imbornales() -> dict:
    return {}
