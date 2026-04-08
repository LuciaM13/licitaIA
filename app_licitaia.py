"""
Entrypoint de LicitaIA — Calculadora de presupuestos EMASESA.

Responsabilidad única: inicializar la base de datos y definir la navegación.
No contiene lógica de negocio ni cálculo.
"""

from __future__ import annotations

import os

import streamlit as st

from src.infraestructura.db import init_db

ROOT = os.path.dirname(os.path.abspath(__file__))
_LOGO_PATH = os.path.join(ROOT, "data", "static", "cropped-Logo_2024-300x300.png")

init_db()

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
