"""Sub-formularios de tuberias (ABA y SAN).

Cada funcion devuelve un dict con SOLO las columnas que pide; el use case
(``insertar_variante_catalogo``) enriquece con ``red`` y aplica
``_eur_a_cents`` exactamente UNA vez al persistir.
"""

from __future__ import annotations

import streamlit as st


def _form_tuberias_aba() -> dict:
    """Schema: red='ABA', label, tipo, diametro_mm, precio_m."""
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input(
            "Etiqueta (label)",
            key="_inline_tuberias_ABA_label",
            placeholder="PE-100 Ø 110 mm",
        )
        tipo = st.text_input(
            "Tipo (e.g. PE-100, FD)",
            key="_inline_tuberias_ABA_tipo",
            placeholder="PE-100",
        )
    with col2:
        diametro_mm = st.number_input(
            "Diametro (mm)", min_value=1, value=100, step=1,
            key="_inline_tuberias_ABA_dn",
        )
    precio_m = st.number_input(
        "Precio EUR/m (BASE EMASESA)",
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
            "Etiqueta (label)",
            key="_inline_tuberias_SAN_label",
            placeholder="Gres Ø 300 mm",
        )
        tipo = st.text_input(
            "Tipo (e.g. PVC, HM)",
            key="_inline_tuberias_SAN_tipo",
            placeholder="Gres",
        )
    with col2:
        diametro_mm = st.number_input(
            "Diametro (mm)", min_value=1, value=200, step=1,
            key="_inline_tuberias_SAN_dn",
        )
    precio_m = st.number_input(
        "Precio EUR/m (BASE EMASESA)",
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
