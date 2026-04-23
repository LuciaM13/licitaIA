"""Widgets Streamlit reutilizables para la página de cálculo."""

from __future__ import annotations

import streamlit as st

from src.infraestructura.utils import find_item, find_by_label


def input_tuberia(
    prefix: str, catalogo: list, default_longitud: float, default_profundidad: float,
) -> tuple[dict, float, float]:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        longitud = st.number_input(
            f"{prefix} Longitud (m)", min_value=0.0, value=default_longitud,
            key=f"{prefix}_longitud")
    with c2:
        tipo = st.selectbox(
            f"{prefix} Tipo de tubería",
            sorted({x["tipo"] for x in catalogo}),
            key=f"{prefix}_tipo")
    with c3:
        diametro = st.selectbox(
            f"{prefix} Diámetro (mm)",
            sorted({x["diametro_mm"] for x in catalogo if x["tipo"] == tipo}),
            key=f"{prefix}_diametro")
    with c4:
        profundidad = st.number_input(
            f"{prefix} Profundidad (m)", min_value=0.0, value=default_profundidad,
            key=f"{prefix}_profundidad")
    try:
        item = find_item(catalogo, tipo, diametro)
    except ValueError as e:
        st.error(f"Error en catálogo de tuberías: {e}")
        st.stop()
    st.info(f"Tubería {prefix}: {item['label']} · {item['precio_m']} €/m")
    return item, longitud, profundidad


def input_subbase(red: str, subbases: list) -> tuple[float, dict | None]:
    """Renderiza inputs de sub-base y retorna (espesor, item) o (0.0, None)."""
    if not subbases:
        return 0.0, None
    sb1, sb2 = st.columns(2)
    with sb1:
        espesor = st.number_input(
            f"Espesor sub-base {red} (m)", min_value=0.0, value=0.0, step=0.05,
            format="%.2f", key=f"subbase_{red.lower()}_espesor")
    with sb2:
        if espesor > 0:
            label = st.selectbox(
                f"Material sub-base {red}",
                [x["label"] for x in subbases], key=f"subbase_{red.lower()}_label")
            item = find_by_label(subbases, label)
        else:
            item = None
    return espesor, item
