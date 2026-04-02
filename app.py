"""
Entrypoint multipage de la app EMASESA.

Responsabilidad única: definir las páginas y lanzar la navegación.
"""

from __future__ import annotations

import os

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
_LOGO_PATH = os.path.join(ROOT, "static", "cropped-Logo_2024-300x300.png")

st.set_page_config(
    page_title="Cálculo de presupuestos · EMASESA",
    page_icon=_LOGO_PATH,
    layout="wide",
)

st.logo(_LOGO_PATH)

pg = st.navigation([
    st.Page("pages/calculadora.py", title="Calculadora", icon=":material/calculate:"),
    st.Page("pages/admin_precios.py", title="Administrar precios", icon=":material/edit:"),
])
pg.run()
