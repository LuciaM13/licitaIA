"""Wrapper cacheado de ``cargar_precios`` para la capa Streamlit.

Este módulo vive en ``src/ui/`` intencionalmente: cualquier acoplamiento con
Streamlit (``st.cache_data``) debe quedar en la capa UI, nunca en
infraestructura. Así ``src/infraestructura/precios.py`` se puede ejecutar
desde un script CLI, un notebook o un test sin instanciar Streamlit.

API
---
Exporta ``cargar_precios`` con la misma firma que la versión pura, más el
método ``.clear()`` inyectado por ``st.cache_data``. Las páginas
(``pages/calculadora.py``, ``pages/admin_precios.py``) importan desde aquí.
"""

from __future__ import annotations

import streamlit as st

from src.infraestructura.precios import cargar_precios as _cargar_precios_sin_cache


@st.cache_data(ttl=60)
def cargar_precios() -> dict:
    """Versión cacheada (TTL 60s) de ``cargar_precios()`` pura.

    Invalidación manual: ``cargar_precios.clear()`` tras escribir desde admin.
    """
    return _cargar_precios_sin_cache()
