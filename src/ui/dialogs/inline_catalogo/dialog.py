"""``@st.dialog`` único + dispatcher de sub-formularios.

Streamlit limita a 1 ``@st.dialog`` por script run; ese es ``render_inline_create_dialog``.
El dispatcher elige el sub-formulario adecuado según el ``target`` que la
calculadora ha pedido (ver ``mappings._TARGET_A_TABLA``).
"""

from __future__ import annotations

import logging

import streamlit as st

from src.catalogo.editor import (
    insertar_calzada_con_espesor,
    insertar_variante_catalogo,
)
from src.ui.dialogs.inline_catalogo.forms_pavimentos import (
    _form_acerados,
    _form_bordillos,
    _form_calzadas,
    _form_demolicion,
)
from src.ui.dialogs.inline_catalogo.forms_tuberias import (
    _form_tuberias_aba,
    _form_tuberias_san,
)
from src.ui.dialogs.inline_catalogo.mappings import _DEMOLICION_CTX, _TARGET_A_TABLA
from src.ui.precios_cache import cargar_precios
from src.ui.session import claves as sk

logger = logging.getLogger(__name__)


def _cerrar_dialog() -> None:
    """Limpia las claves de session_state asociadas al dialog inline.

    Delega en ``sk.disarm_inline_dialog`` para mantener simétricas las
    3 claves del watchdog. Se invoca desde:
      - El callback ``on_dismiss`` del ``@st.dialog`` (ruta feliz: cuando
        Streamlit lo dispara correctamente al cerrar con X / Escape).
      - Las ramas de cierre programático (Cancelar / Sí, crear) dentro
        del cuerpo del dialog.
    """
    sk.disarm_inline_dialog(st.session_state)


@st.dialog("Nueva variante de catálogo", width="large", on_dismiss=_cerrar_dialog)
def render_inline_create_dialog() -> None:
    # WATCHDOG: confirmar al check de la página que el cuerpo del dialog
    # SÍ se está renderizando en este rerun. Si en un rerun futuro el
    # dialog está armado pero esta línea no se ejecuta (porque Streamlit
    # cerró con X y no re-instancia el cuerpo), `RENDER_TICK < OPEN_TICK`
    # y la página limpia el target. Ver `pages/calculadora.py`.
    st.session_state[sk.INLINE_DIALOG_RENDER_TICK] = (
        st.session_state.get(sk.INLINE_DIALOG_OPEN_TICK, 0)
    )
    st.session_state[sk.INLINE_DIALOG_ARMED] = False

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
            _cerrar_dialog()
            st.rerun()
        return

    tabla, red = _TARGET_A_TABLA[target]
    st.caption(f"Tabla: {tabla}" + (f" - Red: {red}" if red else ""))

    item = _dispatch_form(target)

    if st.session_state.get(sk.INLINE_CREATE_CONFIRMAR):
        st.warning("Revisa la variante antes de crearla.")
        for campo, valor in item.items():
            st.write(f"- {campo}: {valor!r}")

        col_si, col_no = st.columns([1, 1])
        with col_si:
            confirmar = st.button(
                "Si, crear",
                type="primary",
                use_container_width=True,
                key=f"_inline_confirmar_{target}",
            )
        with col_no:
            cancelar_confirmacion = st.button(
                "Cancelar",
                use_container_width=True,
                key=f"_inline_cancelar_confirmacion_{target}",
            )

        if cancelar_confirmacion:
            _cerrar_dialog()
            st.rerun()

        if confirmar:
            try:
                # Caso especial: calzada en m³ requiere espesor (FK a
                # espesores_calzada). Se persisten ambas filas en una
                # transacción atómica vía `insertar_calzada_con_espesor`.
                if (
                    tabla == "calzadas"
                    and item.get("unidad") == "m3"
                    and "espesor_m" in item
                ):
                    espesor_m = item.pop("espesor_m")
                    insertar_calzada_con_espesor(
                        item, espesor_m=espesor_m, actor="usuario_inline"
                    )
                else:
                    insertar_variante_catalogo(
                        tabla, red, item, actor="usuario_inline"
                    )
            except ValueError as exc:
                st.error(str(exc))
                return
            # Etiqueta del result para auto-selección post-insert. Cada
            # selectbox de la calculadora lista uno de estos campos según el
            # catálogo (label vs tipo vs material).
            if tabla == "demolicion":
                etiqueta = item.get("material") or ""
            else:
                etiqueta = item.get("label") or item.get("tipo") or ""
            cargar_precios.clear()
            st.session_state[sk.INLINE_CREATE_RESULT] = (tabla, red, etiqueta)
            _cerrar_dialog()
            logger.info(
                "inline_create OK -> tabla=%s, red=%s, etiqueta=%s",
                tabla, red, etiqueta,
            )
            st.rerun()
        return

    col_g, col_c = st.columns([1, 1])
    with col_g:
        revisar = st.button(
            "Revisar alta",
            type="primary",
            use_container_width=True,
            key=f"_inline_revisar_{target}",
        )
    with col_c:
        cancelar = st.button(
            "Cancelar",
            use_container_width=True,
            key=f"_inline_cancelar_{target}",
        )

    if cancelar:
        _cerrar_dialog()
        st.rerun()

    if revisar:
        st.session_state[sk.INLINE_CREATE_CONFIRMAR] = True
        st.rerun()


def _dispatch_form(target: str) -> dict:
    """Despacha al sub-formulario `_form_*` que corresponde al `target`."""
    # Los 5 targets de demolición comparten función con dispatch interno por
    # contexto (tipo_elemento + unidad), porque el form pre-rellena unidad y
    # quiere auto-seleccionar solo en el selectbox que originó el insert.
    if target in _DEMOLICION_CTX:
        return _form_demolicion(target)

    dispatch = {
        "tuberias_aba": _form_tuberias_aba,
        "tuberias_san": _form_tuberias_san,
        "acerados_aba": _form_acerados,
        "acerados_san": _form_acerados,
        "bordillos":    _form_bordillos,
        "calzadas":     _form_calzadas,
    }
    fn = dispatch.get(target)
    if fn is None:
        return {}
    return fn()
