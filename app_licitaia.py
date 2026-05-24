"""
Entrypoint de LicitaIA - Calculadora de presupuestos EMASESA.

Responsabilidad única: inicializar la base de datos y definir la navegación.
No contiene lógica de negocio ni cálculo.
"""

from __future__ import annotations

import logging
import os

import streamlit as st

from src.almacenamiento import init_db
from src.ui.theme import inject_global_styles

# ── Logging global ────────────────────────────────────────────────────────────
# Nivel configurable vía variable de entorno LOG_LEVEL (default INFO).
# DEBUG muestra todo el detalle de cálculos, decisiones y valores intermedios;
# en producción conviene INFO/WARNING para no filtrar config financiera a stdout.
_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
_level = getattr(logging, _level_name, logging.INFO)
logging.basicConfig(
    level=_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.info("LicitaIA arrancando - logging a nivel %s", _level_name)

ROOT = os.path.dirname(os.path.abspath(__file__))
_LOGO_PATH = os.path.join(ROOT, "data", "static", "cropped-Logo_2024-300x300.png")


@st.cache_resource
def _init_db_once() -> None:
    """Ejecuta ``init_db()`` una sola vez por proceso Streamlit.

    Sin este gate, cada rerun del script vuelve a ejecutar el DDL completo y
    toma write-lock en SQLite — innecesario y costoso. ``@st.cache_resource``
    es el patrón idiomático para inicializaciones de tipo singleton.
    """
    init_db()


_init_db_once()

st.set_page_config(
    page_title="LicitaIA · Presupuestos EMASESA",
    page_icon=_LOGO_PATH,
    layout="wide",
)

inject_global_styles()

st.logo(_LOGO_PATH, size="large")

pg = st.navigation([
    st.Page("pages/calculadora.py", title="Calculadora", icon=":material/calculate:"),
    st.Page("pages/historial.py", title="Historial", icon=":material/history:"),
    st.Page("pages/configuracion_catalogo.py", title="Configuración y catálogo", icon=":material/settings:"),
])
pg.run()
