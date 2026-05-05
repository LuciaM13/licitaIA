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
# Sub-formularios contra el schema real (BLOCK 1 fix)
# ---------------------------------------------------------------------------
# Regla maestra: cada sub-form rellena exactamente las columnas NOT NULL sin
# DEFAULT que su tabla declara en src/infraestructura/db/schema.py. Ningún
# form pide columnas que no existan en el schema real. El form devuelve un
# dict con SOLO las columnas que pide; el use case enriquece con `red` y
# aplica `_eur_a_cents` exactamente UNA vez.

def _form_tuberias_aba() -> dict:
    """Schema: red='ABA', label, tipo, diametro_mm, precio_m."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input(
            "Etiqueta (label)", key="_inline_tuberias_ABA_label"
        )
        tipo = st.text_input(
            "Tipo (e.g. PE-100, FD)", key="_inline_tuberias_ABA_tipo"
        )
    with col2:
        diametro_mm = st.number_input(
            "Diámetro (mm)", min_value=1, value=100, step=1,
            key="_inline_tuberias_ABA_dn",
        )
    precio_m = st.number_input(
        "Precio €/m (BASE EMASESA)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_tuberias_ABA_precio_m",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "tipo": tipo.strip(),
        "diametro_mm": int(diametro_mm),
        "precio_m": float(precio_m),
    }


def _form_tuberias_san() -> dict:
    """Schema: red='SAN', label, tipo, diametro_mm, precio_m."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input(
            "Etiqueta (label)", key="_inline_tuberias_SAN_label"
        )
        tipo = st.text_input(
            "Tipo (e.g. PVC, HM)", key="_inline_tuberias_SAN_tipo"
        )
    with col2:
        diametro_mm = st.number_input(
            "Diámetro (mm)", min_value=1, value=200, step=1,
            key="_inline_tuberias_SAN_dn",
        )
    precio_m = st.number_input(
        "Precio €/m (BASE EMASESA)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_tuberias_SAN_precio_m",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "tipo": tipo.strip(),
        "diametro_mm": int(diametro_mm),
        "precio_m": float(precio_m),
    }


def _form_valvuleria() -> dict:
    """Schema: label UNIQUE, tipo, dn_min, dn_max, precio, intervalo_m, instalacion (NULLABLE)."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input("Etiqueta (label)", key="_inline_valvuleria_label")
        tipo = st.text_input("Tipo de pieza", key="_inline_valvuleria_tipo")
    with col2:
        dn_min = st.number_input(
            "DN mínimo (mm)", min_value=1, value=60, step=1,
            key="_inline_valvuleria_dn_min",
        )
        dn_max = st.number_input(
            "DN máximo (mm)", min_value=int(dn_min),
            value=max(int(dn_min), 200), step=1,
            key="_inline_valvuleria_dn_max",
        )
    col3, col4 = st.columns(2)
    with col3:
        intervalo_m = st.number_input(
            "Intervalo (m)", min_value=0.01, value=100.0, step=1.0,
            format="%.2f", key="_inline_valvuleria_intervalo",
        )
        instalacion = st.selectbox(
            "Instalación",
            ["(sin distinción)", "enterrada", "pozo"],
            key="_inline_valvuleria_instalacion",
        )
    with col4:
        precio = st.number_input(
            "Precio €/ud (BASE EMASESA)",
            min_value=0.0, value=0.0, step=0.01, format="%.2f",
            key="_inline_valvuleria_precio",
        )
        st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "tipo": tipo.strip(),
        "dn_min": int(dn_min),
        "dn_max": int(dn_max),
        "intervalo_m": float(intervalo_m),
        "instalacion": None if instalacion == "(sin distinción)" else instalacion,
        "precio": float(precio),
    }


def _form_acometidas() -> dict:
    """Schema: red, tipo, precio. UNIQUE(red, tipo). NO tiene label ni diametro."""
    tipo = st.text_input(
        "Tipo de acometida", key="_inline_acometidas_tipo",
        help="Identificador libre. UNIQUE por (red, tipo).",
    )
    precio = st.number_input(
        "Precio €/ud (BASE EMASESA)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_acometidas_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "tipo": tipo.strip(),
        "precio": float(precio),
    }


def _form_acerados() -> dict:
    """Schema: red, label, unidad CHECK IN ('m','m2','m3','ud'), precio."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input("Etiqueta (label)", key="_inline_acerados_label")
    with col2:
        unidad = st.selectbox(
            "Unidad", ["m", "m2", "m3", "ud"], index=1,
            key="_inline_acerados_unidad",
        )
    precio = st.number_input(
        "Precio (BASE EMASESA, en € por unidad seleccionada)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_acerados_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "unidad": unidad,
        "precio": float(precio),
    }


def _form_bordillos() -> dict:
    """Schema: label UNIQUE, unidad CHECK IN ('m','m2','ud'), precio."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input("Etiqueta (label)", key="_inline_bordillos_label")
    with col2:
        unidad = st.selectbox(
            "Unidad", ["m", "m2", "ud"], index=0,
            key="_inline_bordillos_unidad",
        )
    precio = st.number_input(
        "Precio (BASE EMASESA, en € por unidad)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_bordillos_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "unidad": unidad,
        "precio": float(precio),
    }


def _form_calzadas() -> dict:
    """Schema: label UNIQUE, unidad CHECK IN ('m2','m3'), precio."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input("Etiqueta (label)", key="_inline_calzadas_label")
    with col2:
        unidad = st.selectbox(
            "Unidad", ["m2", "m3"], index=0,
            key="_inline_calzadas_unidad",
        )
    precio = st.number_input(
        "Precio (BASE EMASESA, en € por unidad)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_calzadas_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "unidad": unidad,
        "precio": float(precio),
    }


def _form_pozos() -> dict:
    """Schema: label, precio, intervalo (NOT NULL). El resto opcional/DEFAULT."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input("Etiqueta (label)", key="_inline_pozos_label")
    with col2:
        intervalo = st.number_input(
            "Intervalo (m)", min_value=0.01, value=100.0, step=1.0,
            format="%.2f", key="_inline_pozos_intervalo",
        )
    precio = st.number_input(
        "Precio €/ud (BASE EMASESA)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_pozos_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "intervalo": float(intervalo),
        "precio": float(precio),
    }


def _form_imbornales() -> dict:
    """Schema: label UNIQUE, precio, tipo CHECK IN ('adaptacion','nuevo')."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input("Etiqueta (label)", key="_inline_imbornales_label")
    with col2:
        tipo = st.selectbox(
            "Tipo", ["adaptacion", "nuevo"], index=0,
            key="_inline_imbornales_tipo",
        )
    precio = st.number_input(
        "Precio €/ud (BASE EMASESA)",
        min_value=0.0, value=0.0, step=0.01, format="%.2f",
        key="_inline_imbornales_precio",
    )
    st.caption("Introduce el precio base EMASESA (sin el margen de seguridad)")
    return {
        "label": label.strip(),
        "tipo": tipo,
        "precio": float(precio),
    }
