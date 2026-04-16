"""
Entrypoint de LicitaIA - Calculadora de presupuestos EMASESA.

Responsabilidad única: inicializar la base de datos y definir la navegación.
No contiene lógica de negocio ni cálculo.
"""

from __future__ import annotations

import logging
import os

import streamlit as st

from src.infraestructura.db import init_db

# ── Logging global ────────────────────────────────────────────────────────────
# DEBUG muestra todo el detalle de cálculos, decisiones y valores intermedios.
# Para producción, cambiar a logging.INFO y solo se verán los hitos principales.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.info("LicitaIA arrancando - logging configurado a nivel DEBUG")

ROOT = os.path.dirname(os.path.abspath(__file__))
_LOGO_PATH = os.path.join(ROOT, "data", "static", "cropped-Logo_2024-300x300.png")

init_db()

st.set_page_config(
    page_title="Cálculo de presupuestos · EMASESA",
    page_icon=_LOGO_PATH,
    layout="wide",
)

st.logo(_LOGO_PATH, size="large")

pg = st.navigation([
    st.Page("pages/calculadora.py", title="Calculadora", icon=":material/calculate:"),
    st.Page("pages/historial.py", title="Historial", icon=":material/history:"),
    st.Page("pages/admin_precios.py", title="Administrar precios", icon=":material/edit:"),
])
pg.run()
